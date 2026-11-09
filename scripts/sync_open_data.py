#!/usr/bin/env python3
"""Refresh static, openly published football datasets; no API key is used."""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SNAPSHOTS = DATA / "competitions"
OPENFOOTBALL = "https://raw.githubusercontent.com/openfootball/football.json/master"
STATSBOMB = "https://raw.githubusercontent.com/hudl/open-data/master/data"

# Current-season OpenFootball result/fixture files. Other directory entries remain
# visible and explicitly show which open datasets do not cover them.
LEAGUES = {
    "premier-league": ("en.1.json", "2026/27"),
    "ligue-1": ("fr.1.json", "2026/27"),
    "la-liga": ("es.1.json", "2026/27"),
    "serie-a": ("it.1.json", "2026/27"),
    "bundesliga": ("de.1.json", "2026/27"),
}

# StatsBomb publishes selected historic seasons. These indexes include match
# records; event and lineup JSON is loaded from the same public static repository
# only when a user opens a supported match.
STATSBOMB_SEASONS = {
    "premier-league": [(2, 44, "2003/04", "2003")],
    "bundesliga": [(9, 281, "2023/24", "2023")],
    "champions-league": [(16, 4, "2018/19", "2018")],
    "fifa-world-cup": [(43, 106, "2022", "2022"), (43, 3, "2018", "2018")],
    "uefa-euro": [(55, 282, "2024", "2024"), (55, 43, "2020", "2020")],
    "copa-america": [(223, 282, "2024", "2024")],
    "afcon": [(1267, 107, "2023", "2023")],
    "la-liga": [(11, 90, "2020/21", "2020")],
    "ligue-1": [(7, 235, "2022/23", "2022")],
    "serie-a": [(12, 27, "2015/16", "2015")],
}


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "football-stats-tracker/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def standings(fixtures):
    table = {}
    for match in fixtures:
        home, away = match["home"], match["away"]
        for team in (home, away):
            table.setdefault(team["id"], {"teamId": team["id"], "team": team["name"], "played": 0, "won": 0, "drawn": 0, "lost": 0, "goalsFor": 0, "goalsAgainst": 0, "points": 0})
        if match["goals"]["home"] is None or match["goals"]["away"] is None:
            continue
        h, a = table[home["id"]], table[away["id"]]
        hg, ag = match["goals"]["home"], match["goals"]["away"]
        h["played"] += 1; a["played"] += 1
        h["goalsFor"] += hg; h["goalsAgainst"] += ag
        a["goalsFor"] += ag; a["goalsAgainst"] += hg
        if hg > ag:
            h["won"] += 1; h["points"] += 3; a["lost"] += 1
        elif hg < ag:
            a["won"] += 1; a["points"] += 3; h["lost"] += 1
        else:
            h["drawn"] += 1; a["drawn"] += 1; h["points"] += 1; a["points"] += 1
    rows = sorted(table.values(), key=lambda r: (r["points"], r["goalsFor"] - r["goalsAgainst"], r["goalsFor"]), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        row["goalDifference"] = row["goalsFor"] - row["goalsAgainst"]
    return rows


def team_statistics(fixtures):
    stats = {}
    for fixture in fixtures:
        for side, other in (("home", "away"), ("away", "home")):
            team = fixture[side]
            row = stats.setdefault(team["id"], {"fixtures": {"played": 0, "wins": 0, "draws": 0, "loses": 0},
                "goals": {"for": {"total": 0}, "against": {"total": 0}}, "clean_sheet": {"total": 0}})
            goals, conceded = fixture["goals"][side], fixture["goals"][other]
            if goals is None or conceded is None:
                continue
            row["fixtures"]["played"] += 1
            row["goals"]["for"]["total"] += goals
            row["goals"]["against"]["total"] += conceded
            if conceded == 0:
                row["clean_sheet"]["total"] += 1
            if goals > conceded:
                row["fixtures"]["wins"] += 1
            elif goals < conceded:
                row["fixtures"]["loses"] += 1
            else:
                row["fixtures"]["draws"] += 1
    return stats


def normalize_openfootball(item, source_file, season_label, fetched_at):
    raw = fetch_json(f"{OPENFOOTBALL}/2026-27/{source_file}")
    fixtures, teams = [], {}
    for index, row in enumerate(raw.get("matches", []), 1):
        home_name, away_name = row.get("team1"), row.get("team2")
        if not home_name or not away_name:
            continue
        home_id, away_id = slug(home_name), slug(away_name)
        teams[home_id] = {"id": home_id, "name": home_name, "country": item.get("country")}
        teams[away_id] = {"id": away_id, "name": away_name, "country": item.get("country")}
        ft = (row.get("score") or {}).get("ft") or [None, None]
        ht = (row.get("score") or {}).get("ht") or [None, None]
        played = len(ft) >= 2 and ft[0] is not None and ft[1] is not None
        fixtures.append({
            "id": f"openfootball-{item['id']}-{index}", "date": row.get("date"), "timestamp": None,
            "round": row.get("round"), "status": "FT" if played else "NS", "statusLong": "Finished" if played else "Scheduled",
            "home": {"id": home_id, "name": home_name}, "away": {"id": away_id, "name": away_name},
            "goals": {"home": ft[0] if played else None, "away": ft[1] if played else None},
            "halftime": {"home": ht[0] if len(ht) >= 2 else None, "away": ht[1] if len(ht) >= 2 else None},
        })
    fixtures.sort(key=lambda f: f.get("date") or "")
    snapshot = {
        "schemaVersion": 2, "competition": {"id": item["id"], "name": item["name"], "country": item.get("country")},
        "season": season_label, "seasonLabel": season_label, "provider": "OpenFootball (CC0)", "sourceUrl": f"https://github.com/openfootball/football.json/tree/master/2026-27",
        "generatedAt": fetched_at, "fixtures": fixtures, "teams": list(teams.values()), "standings": standings(fixtures),
        "teamStats": team_statistics(fixtures),
        "players": [], "topScorers": [],
        "coverage": {"fixtures": {"available": bool(fixtures), "rows": len(fixtures), "fetchedAt": fetched_at},
                     "standings": {"available": bool(fixtures), "rows": len(standings(fixtures)), "fetchedAt": fetched_at, "note": "Calculated from completed OpenFootball results."},
                     "teams": {"available": bool(teams), "rows": len(teams), "fetchedAt": fetched_at},
                     "players": {"available": False, "rows": 0, "note": "OpenFootball does not publish player statistics."},
                     "topScorers": {"available": False, "rows": 0, "note": "OpenFootball does not publish player statistics."}},
    }
    write_json(SNAPSHOTS / f"{item['id']}-{season_label[:4]}.json", snapshot)
    return snapshot


def normalize_statsbomb(item, comp_id, season_id, label, season_key, fetched_at):
    matches = fetch_json(f"{STATSBOMB}/matches/{comp_id}/{season_id}.json")
    fixtures, teams = [], {}
    for row in matches:
        home = row.get("home_team", {}); away = row.get("away_team", {})
        home_name, away_name = home.get("home_team_name"), away.get("away_team_name")
        if not home_name or not away_name:
            continue
        home_id = f"sb-{home.get('home_team_id', slug(home_name))}"
        away_id = f"sb-{away.get('away_team_id', slug(away_name))}"
        teams[home_id] = {"id": home_id, "name": home_name}
        teams[away_id] = {"id": away_id, "name": away_name}
        fixtures.append({"id": f"statsbomb-{row['match_id']}", "statsbombMatchId": row["match_id"], "date": row.get("match_date"), "timestamp": None,
                         "round": (row.get("competition_stage") or {}).get("name"), "status": "FT", "statusLong": "Finished",
                         "home": {"id": home_id, "name": home_name}, "away": {"id": away_id, "name": away_name},
                         "goals": {"home": row.get("home_score"), "away": row.get("away_score")}})
    fixtures.sort(key=lambda f: f.get("date") or "")
    snapshot = {"schemaVersion": 2, "competition": {"id": item["id"], "name": item["name"], "country": item.get("country")},
                "season": season_key, "seasonLabel": label, "provider": "StatsBomb Open Data", "sourceUrl": "https://github.com/hudl/open-data",
                "generatedAt": fetched_at, "fixtures": fixtures, "teams": list(teams.values()), "standings": [], "teamStats": team_statistics(fixtures), "players": [], "topScorers": [],
                "coverage": {"fixtures": {"available": bool(fixtures), "rows": len(fixtures), "fetchedAt": fetched_at},
                             "standings": {"available": False, "rows": 0, "note": "Knockout and selected-season data; no full league table supplied."},
                             "teams": {"available": bool(teams), "rows": len(teams), "fetchedAt": fetched_at},
                             "players": {"available": False, "rows": 0, "note": "Player event data is available on supported match pages, not as full season totals."},
                             "topScorers": {"available": False, "rows": 0, "note": "No full season scorer table is supplied."}}}
    write_json(SNAPSHOTS / f"{item['id']}-{season_key}.json", snapshot)
    return snapshot


def main():
    fetched_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    index = json.loads((DATA / "competitions.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in index}
    coverage = {"schemaVersion": 2, "provider": "OpenFootball + StatsBomb Open Data", "status": "partial", "generatedAt": fetched_at,
                "sources": [{"name": "OpenFootball", "url": "https://github.com/openfootball/football.json", "license": "CC0-1.0"},
                            {"name": "StatsBomb Open Data", "url": "https://github.com/hudl/open-data", "license": "Attribution required"}],
                "competitions": {}, "message": "Static open datasets; current fixtures and results are limited to the listed OpenFootball leagues. Historical event data is available for selected StatsBomb seasons. Other sections stay unavailable where no open file source covers them."}
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    for comp_id, (filename, season_label) in LEAGUES.items():
        item = by_id.get(comp_id)
        if not item:
            continue
        try:
            snap = normalize_openfootball(item, filename, season_label, fetched_at)
            coverage["competitions"].setdefault(comp_id, {"seasons": []})["seasons"].append(season_label[:4])
            for section, state in snap["coverage"].items():
                coverage["competitions"][comp_id][section] = state
        except Exception as exc:
            coverage["competitions"].setdefault(comp_id, {"seasons": []})["fixtures"] = {"available": False, "note": f"OpenFootball file could not be refreshed: {exc}"}
    for comp_id, seasons in STATSBOMB_SEASONS.items():
        item = by_id.get(comp_id)
        if not item:
            continue
        for source_comp, source_season, label, season_key in seasons:
            try:
                snap = normalize_statsbomb(item, source_comp, source_season, label, season_key, fetched_at)
                row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
                row["seasons"].append(season_key)
                for section, state in snap["coverage"].items():
                    if state.get("available"):
                        row[section] = state
                row["statsbomb"] = {"available": True, "rows": len(snap["fixtures"]), "fetchedAt": fetched_at, "season": label}
            except Exception as exc:
                coverage["competitions"].setdefault(comp_id, {"seasons": []})["statsbomb"] = {"available": False, "note": f"StatsBomb match list unavailable: {exc}"}
    for row in coverage["competitions"].values():
        row["seasons"] = sorted(set(row.get("seasons", [])), reverse=True)
    write_json(DATA / "coverage.json", coverage)
    print(json.dumps({"sources": 2, "competitions_with_files": len(coverage["competitions"]), "status": coverage["status"]}, indent=2))


if __name__ == "__main__":
    main()
