#!/usr/bin/env python3
"""Fetch a quota-aware, auditable set of API-Football snapshots."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "competitions.json"
COVERAGE_PATH = ROOT / "data" / "coverage.json"
MAP_PATH = ROOT / "data" / "provider-map.json"
SNAPSHOT_DIR = ROOT / "data" / "competitions"
BASE_URL = "https://v3.football.api-sports.io"
GROUPS = ["standings", "fixtures", "teams", "topScorers", "players", "teamStats", "fixtureStats", "events", "lineups"]
DEFAULT_BUDGET = 90  # leaves headroom below the provider's advertised 100/day free quota


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


class Api:
    def __init__(self, key: str, budget: int):
        self.key = key
        self.budget = budget
        self.count = 0
        self.remaining = None

    def get(self, endpoint: str, params: dict):
        if self.count >= self.budget:
            raise RuntimeError("Daily API request budget reached")
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"x-apisports-key": self.key, "User-Agent": "football-stats-tracker/1.0"})
        last_error = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    self.count += 1
                    try:
                        self.remaining = int(response.headers.get("x-ratelimit-requests-remaining", ""))
                    except ValueError:
                        pass
                    errors = payload.get("errors")
                    if errors:
                        raise RuntimeError(str(errors))
                    return payload
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:400]}"
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = str(exc)
                if attempt == 2:
                    break
            time.sleep(2 ** attempt)
        raise RuntimeError(last_error or "Provider request failed")


def discover_league(api: Api, item: dict):
    names = item.get("providerSearchTerms") or [item["name"]]
    exact = []
    seen = set()
    for name in names:
        payload = api.get("leagues", {"search": name})
        for entry in payload.get("response", []):
            candidate_id = entry.get("league", {}).get("id")
            candidate_name = entry.get("league", {}).get("name", "")
            if candidate_id not in seen and normalize(candidate_name) in {normalize(item["name"]), *(normalize(term) for term in names)}:
                exact.append(entry)
                seen.add(candidate_id)
    country = item.get("country", "")
    if country not in ("Europe", "International", "South America", "Africa", "Asia", "North & Central America"):
        exact_country = [entry for entry in exact if normalize(entry.get("country", {}).get("name", "")) == normalize(country)]
        if exact_country:
            exact = exact_country
    if len(exact) != 1:
        raise RuntimeError(f"League lookup was ambiguous ({len(exact)} exact candidates); pin the provider league ID before syncing")
    chosen = exact[0]
    seasons = chosen.get("seasons", [])
    return {
        "id": chosen.get("league", {}).get("id"),
        "name": chosen.get("league", {}).get("name"),
        "country": chosen.get("country", {}).get("name"),
        "logo": chosen.get("league", {}).get("logo"),
        "seasons": [{"year": s.get("year"), "start": s.get("start"), "end": s.get("end"), "current": s.get("current")} for s in seasons],
    }


def flatten_standings(payload):
    rows = []
    for response in payload.get("response", []):
        league = response.get("league", {})
        for table in league.get("standings", []) or []:
            for row in table:
                rows.append({
                    "rank": row.get("rank"), "teamId": row.get("team", {}).get("id"), "team": row.get("team", {}).get("name"),
                    "logo": row.get("team", {}).get("logo"), "played": row.get("all", {}).get("played"),
                    "won": row.get("all", {}).get("win"), "drawn": row.get("all", {}).get("draw"), "lost": row.get("all", {}).get("lose"),
                    "goalsFor": row.get("all", {}).get("goals", {}).get("for"), "goalsAgainst": row.get("all", {}).get("goals", {}).get("against"),
                    "goalDifference": row.get("goalsDiff"), "points": row.get("points"), "form": row.get("form"), "description": row.get("description"),
                })
    return rows


def normalize_fixture(row):
    fixture = row.get("fixture", {})
    teams = row.get("teams", {})
    goals = row.get("goals", {})
    score = row.get("score", {})
    return {
        "id": fixture.get("id"), "date": fixture.get("date"), "timestamp": fixture.get("timestamp"),
        "timezone": fixture.get("timezone"), "venue": fixture.get("venue", {}).get("name"),
        "round": row.get("league", {}).get("round"), "status": fixture.get("status", {}).get("short"),
        "statusLong": fixture.get("status", {}).get("long"), "elapsed": fixture.get("status", {}).get("elapsed"),
        "home": {"id": teams.get("home", {}).get("id"), "name": teams.get("home", {}).get("name"), "logo": teams.get("home", {}).get("logo")},
        "away": {"id": teams.get("away", {}).get("id"), "name": teams.get("away", {}).get("name"), "logo": teams.get("away", {}).get("logo")},
        "goals": {"home": goals.get("home"), "away": goals.get("away")},
        "halftime": {"home": score.get("halftime", {}).get("home"), "away": score.get("halftime", {}).get("away")},
        "fulltime": {"home": score.get("fulltime", {}).get("home"), "away": score.get("fulltime", {}).get("away")},
        "extratime": score.get("extratime"), "penalty": score.get("penalty"),
    }


def normalize_team(row):
    team = row.get("team", {})
    venue = row.get("venue", {})
    return {"id": team.get("id"), "name": team.get("name"), "code": team.get("code"), "country": team.get("country"), "founded": team.get("founded"), "national": team.get("national"), "logo": team.get("logo"), "venue": {"id": venue.get("id"), "name": venue.get("name"), "city": venue.get("city"), "capacity": venue.get("capacity"), "surface": venue.get("surface"), "image": venue.get("image")}}


def normalize_player(row):
    player = row.get("player", {})
    stats = (row.get("statistics") or [{}])[0]
    games, goals, shots, passes, tackles, duels, dribbles, fouls, cards, penalty = (stats.get(key) or {} for key in ("games", "goals", "shots", "passes", "tackles", "duels", "dribbles", "fouls", "cards", "penalty"))
    return {
        "id": player.get("id"), "name": player.get("name"), "firstname": player.get("firstname"), "lastname": player.get("lastname"),
        "age": player.get("age"), "nationality": player.get("nationality"), "height": player.get("height"), "weight": player.get("weight"),
        "photo": player.get("photo"), "teamId": stats.get("team", {}).get("id"), "team": stats.get("team", {}).get("name"),
        "position": games.get("position"), "appearances": games.get("appearences"), "lineups": games.get("lineups"),
        "minutes": games.get("minutes"), "rating": games.get("rating"), "captain": games.get("captain"),
        "goals": goals.get("total"), "assists": goals.get("assists"), "conceded": goals.get("conceded"), "saves": goals.get("saves"),
        "shots": shots.get("total"), "shotsOnTarget": shots.get("on"), "passes": passes.get("total"), "keyPasses": passes.get("key"), "passAccuracy": passes.get("accuracy"),
        "tackles": tackles.get("total"), "blocks": tackles.get("blocks"), "interceptions": tackles.get("interceptions"), "duelsWon": duels.get("won"), "duelsTotal": duels.get("total"),
        "dribbles": dribbles.get("success"), "dribblesAttempted": dribbles.get("attempts"), "foulsDrawn": fouls.get("drawn"), "foulsCommitted": fouls.get("committed"),
        "yellowCards": cards.get("yellow"), "redCards": cards.get("red"), "penaltiesScored": penalty.get("scored"), "penaltiesMissed": penalty.get("missed"),
    }


def save_section(snapshot: dict, group: str, payload: dict, stamp: str, page: int | None = None):
    response = payload.get("response", [])
    if group == "standings":
        snapshot[group] = flatten_standings(payload)
    elif group == "fixtures":
        snapshot[group] = [normalize_fixture(row) for row in response]
        snapshot[group].sort(key=lambda row: row.get("timestamp") or 0)
    elif group == "teams":
        snapshot[group] = [normalize_team(row) for row in response]
    elif group == "topScorers":
        snapshot[group] = [normalize_player(row) for row in response]
    elif group == "players":
        pages = snapshot.setdefault("playerPages", {})
        pages[str(page)] = [normalize_player(row) for row in response]
        snapshot[group] = list({str(player.get("id")): player for rows in pages.values() for player in rows if player.get("id")}.values())
        snapshot["playerPagination"] = payload.get("paging", {})
        snapshot["nextPlayerPage"] = (page + 1) if page < int(payload.get("paging", {}).get("total", page) or page) else 1
    elif group == "teamStats":
        team = payload.get("_team_id")
        snapshot.setdefault(group, {})[str(team)] = response or None
    elif group == "fixtureStats":
        fixture = payload.get("_fixture_id")
        stats = []
        for team_block in response:
            stats.append({"teamId": team_block.get("team", {}).get("id"), "team": team_block.get("team", {}).get("name"), "statistics": {row.get("type"): row.get("value") for row in team_block.get("statistics", [])}})
        snapshot.setdefault(group, {})[str(fixture)] = stats
    elif group == "events":
        fixture = payload.get("_fixture_id")
        snapshot.setdefault(group, {})[str(fixture)] = [{"time": row.get("time"), "team": row.get("team", {}).get("name"), "teamId": row.get("team", {}).get("id"), "player": row.get("player", {}).get("name"), "playerId": row.get("player", {}).get("id"), "assist": row.get("assist", {}).get("name"), "type": row.get("type"), "detail": row.get("detail"), "comments": row.get("comments")} for row in response]
    elif group == "lineups":
        fixture = payload.get("_fixture_id")
        snapshot.setdefault(group, {})[str(fixture)] = [{"team": row.get("team", {}).get("name"), "teamId": row.get("team", {}).get("id"), "formation": row.get("formation"), "coach": row.get("coach", {}).get("name"), "startXI": [{"id": p.get("player", {}).get("id"), "name": p.get("player", {}).get("name"), "number": p.get("player", {}).get("number"), "position": p.get("player", {}).get("pos"), "grid": p.get("player", {}).get("grid")} for p in row.get("startXI", [])], "substitutes": [{"id": p.get("player", {}).get("id"), "name": p.get("player", {}).get("name"), "number": p.get("player", {}).get("number"), "position": p.get("player", {}).get("pos")} for p in row.get("substitutes", [])]} for row in response]
    dataset = snapshot.get(group, [])
    rows = len(dataset) if isinstance(dataset, (list, dict)) else 0
    snapshot.setdefault("coverage", {})[group] = {"available": bool(response), "fetchedAt": stamp, "rows": rows, "note": None if response else "The provider returned no rows for this competition and season."}


def main():
    key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    if not key:
        print("API_FOOTBALL_KEY is not configured; leaving all data marked unavailable.")
        return 0
    index = read_json(INDEX_PATH, [])
    budget = max(1, min(7500, int(os.environ.get("API_REQUEST_BUDGET", DEFAULT_BUDGET))))
    api = Api(key, budget)
    provider_map = read_json(MAP_PATH, {"provider": "API-Football", "competitions": {}})
    provider_map.setdefault("competitions", {})
    today = dt.datetime.now(dt.timezone.utc)
    group = os.environ.get("SYNC_GROUP", "").strip() or GROUPS[(today.timetuple().tm_yday - 1) % len(GROUPS)]
    if group not in GROUPS:
        print(f"Unknown SYNC_GROUP: {group}; expected one of {', '.join(GROUPS)}", file=sys.stderr)
        return 2
    stamp = today.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    coverage = read_json(COVERAGE_PATH, {"schemaVersion": 1, "competitions": {}})
    coverage.update({"schemaVersion": 1, "provider": "API-Football", "status": "syncing", "generatedAt": stamp, "lastSyncGroup": group, "requestCount": 0, "message": "Snapshots are published per competition and section; check each section's fetch time and source coverage."})
    errors = []
    season_override = os.environ.get("SYNC_SEASON", "").strip()
    for item in index:
        if api.count >= budget:
            break
        comp_id = item["id"]
        mapping = provider_map["competitions"].get(comp_id)
        if not mapping or not mapping.get("id"):
            try:
                mapping = discover_league(api, item)
                if not mapping.get("id"):
                    raise RuntimeError("Provider match did not include a league ID")
                provider_map["competitions"][comp_id] = mapping
                write_json(MAP_PATH, provider_map)
            except Exception as exc:
                errors.append({"competition": comp_id, "section": "provider mapping", "error": str(exc)})
                coverage.setdefault("competitions", {}).setdefault(comp_id, {})["mapping"] = {"available": False, "fetchedAt": stamp, "note": str(exc)}
                continue
        source_season = int(season_override or str(item.get("season", "2026"))[:4])
        snapshot_path = SNAPSHOT_DIR / f"{comp_id}-{source_season}.json"
        snapshot = read_json(snapshot_path, {"schemaVersion": 1, "competition": {"id": comp_id, "name": item["name"], "country": item.get("country"), "group": item.get("group")}, "season": source_season, "seasonLabel": item.get("season"), "provider": "API-Football", "providerLeagueId": mapping["id"], "generatedAt": stamp, "coverage": {}})
        snapshot["generatedAt"] = stamp
        params = {"league": mapping["id"], "season": source_season}
        if group == "teamStats":
            teams = snapshot.get("teams", [])
            progress = int(snapshot.get("nextTeamStatsIndex", 0))
            while progress < len(teams) and api.count < budget:
                team = teams[progress]
                try:
                    payload = api.get("teams/statistics", {**params, "team": team["id"]})
                    payload["_team_id"] = team["id"]
                    save_section(snapshot, group, payload, stamp)
                    progress += 1
                    snapshot["nextTeamStatsIndex"] = progress if progress < len(teams) else 0
                    write_json(snapshot_path, snapshot)
                except Exception as exc:
                    errors.append({"competition": comp_id, "section": group, "team": team.get("name"), "error": str(exc)})
                    break
        elif group in ("fixtureStats", "events", "lineups"):
            matches = [fixture for fixture in snapshot.get("fixtures", []) if fixture.get("status") in ("FT", "AET", "PEN") and fixture.get("id")]
            index_key = {"fixtureStats":"nextFixtureStatsIndex", "events":"nextEventsIndex", "lineups":"nextLineupsIndex"}[group]
            endpoint = {"fixtureStats":"fixtures/statistics", "events":"fixtures/events", "lineups":"fixtures/lineups"}[group]
            progress = int(snapshot.get(index_key, 0))
            while progress < len(matches) and api.count < budget:
                fixture = matches[progress]
                try:
                    payload = api.get(endpoint, {"fixture": fixture["id"]})
                    payload["_fixture_id"] = fixture["id"]
                    save_section(snapshot, group, payload, stamp)
                    progress += 1
                    snapshot[index_key] = progress if progress < len(matches) else 0
                    write_json(snapshot_path, snapshot)
                except Exception as exc:
                    errors.append({"competition": comp_id, "section": group, "fixture": fixture.get("id"), "error": str(exc)})
                    break
        else:
            page = int(snapshot.get("nextPlayerPage", 1)) if group == "players" else None
            query = {**params, **({"page": page} if page else {})}
            try:
                payload = api.get({"topScorers": "players/topscorers"}.get(group, group), query)
                save_section(snapshot, group, payload, stamp, page)
                write_json(snapshot_path, snapshot)
            except Exception as exc:
                errors.append({"competition": comp_id, "section": group, "error": str(exc)})
        coverage.setdefault("competitions", {}).setdefault(comp_id, {})[group] = snapshot.get("coverage", {}).get(group, {"available": False, "fetchedAt": stamp, "note": "Budget reached before this section was refreshed."})
        coverage["competitions"][comp_id].update({"season": source_season, "providerLeagueId": mapping["id"], "providerLeagueName": mapping.get("name"), "mappingFetchedAt": coverage["competitions"][comp_id].get("mapping", {}).get("fetchedAt")})
    write_json(MAP_PATH, provider_map)
    coverage["requestCount"] = api.count
    coverage["requestBudget"] = budget
    coverage["providerQuotaRemaining"] = api.remaining
    coverage["errors"] = errors
    coverage["status"] = "partial" if errors or api.count >= budget else "ready"
    coverage["message"] = "Data coverage varies by competition and section. A missing field is not a zero; review source and fetch time in each snapshot."
    write_json(COVERAGE_PATH, coverage)
    print(json.dumps({"group": group, "requests": api.count, "budget": budget, "remaining": api.remaining, "errors": len(errors), "status": coverage["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
