#!/usr/bin/env python3
"""Refresh static, openly published football datasets; no API key is used."""
from __future__ import annotations

import datetime as dt
import csv
import json
import math
import re
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SNAPSHOTS = DATA / "competitions"
OPENFOOTBALL = "https://raw.githubusercontent.com/openfootball/football.json/master"
STATSBOMB = "https://raw.githubusercontent.com/hudl/open-data/master/data"
OPENPLAY_RELEASES = "https://api.github.com/repos/nlbair/openplay/releases/tags/data-v0.1.0"
OPEN_MATCHDAY = "https://raw.githubusercontent.com/oladeeayo/open-matchday/master/data"
CORNERFLICK_SEASON = "https://cornerflick.com/football/leagues/ekstraklasa/results/season.json"
OPENPLAY_COMPS = {
    "eng": "premier-league", "esp": "la-liga", "ita": "serie-a", "ger": "bundesliga", "fra": "ligue-1",
    "ucl": "champions-league", "uel": "europa-league", "wc": "fifa-world-cup", "euro": "uefa-euro",
    "copa": "copa-america", "afcon": "afcon", "nla": "nations-league", "nlb": "nations-league",
}
PLAYER_FIELDS = ["touches", "passes", "passes_completed", "passes_final_third", "passes_into_box", "progressive_passes", "crosses", "through_balls", "key_passes", "assists", "xa", "shots", "shots_on_target", "shots_off_target", "shots_blocked", "goals", "headed_goals", "penalty_goals", "own_goals", "xg", "npxg", "dribbles", "dribbles_completed", "tackles", "tackles_won", "interceptions", "clearances", "ball_recoveries", "aerials", "aerials_won", "fouls_committed", "fouls_won", "offsides", "errors", "saves", "yellow_cards", "second_yellows", "red_cards"]

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


def fetch_csv(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "football-stats-tracker/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return list(csv.DictReader(response.read().decode("utf-8-sig").splitlines()))


def match_stats(home_id, away_id, row, prefix="home", field_labels=None):
    field_labels = field_labels or {}
    values = {}
    for field, label in field_labels.items():
        value = number(row.get(f"{prefix}_{field}"), None)
        if value is not None:
            try:
                number_value = float(value)
                values[label] = int(number_value) if number_value.is_integer() else round(number_value, 2)
            except (TypeError, ValueError):
                values[label] = value
    return values


def normalize_openmatchday(item, season_key, folder, fetched_at):
    base = f"{OPEN_MATCHDAY}/{folder}"
    result_rows = fetch_csv(f"{base}/results_2627.csv")
    fixture_rows = fetch_csv(f"{base}/fixtures_2627.csv")
    merged = {}
    for row in result_rows + fixture_rows:
        key = (row.get("date"), row.get("home"), row.get("away"))
        merged[key] = {**merged.get(key, {}), **{k: v for k, v in row.items() if v not in (None, "")}}
    fixtures, teams, fixture_stats = [], {}, {}
    stat_fields = {"shots":"Shots", "target":"Shots on target", "fouls":"Fouls", "corners":"Corners", "corners_1h":"Corners (1st half)", "corners_2h":"Corners (2nd half)", "yellow":"Yellow cards", "red":"Red cards"}
    for index, row in enumerate(merged.values(), 1):
        home_name = row.get("home", "").strip(); away_name = row.get("away", "").strip()
        if not home_name or not away_name:
            continue
        hid, aid = slug(home_name), slug(away_name)
        teams[hid] = {"id": hid, "name": home_name, "country": item.get("country")}
        teams[aid] = {"id": aid, "name": away_name, "country": item.get("country")}
        gh, ga = score_value(row.get("ft_home")), score_value(row.get("ft_away"))
        finished = gh is not None and ga is not None
        mid = f"openmatchday-{item['id']}-{row.get('date')}-{hid}-{aid}"
        fixtures.append({"id": mid, "date": row.get("date"), "timestamp": None, "round": f"Matchday {row.get('gw')}" if row.get("gw") else None,
                         "status": "FT" if finished else "NS", "statusLong": "Finished" if finished else "Scheduled",
                         "home": {"id": hid, "name": home_name}, "away": {"id": aid, "name": away_name},
                         "goals": {"home": gh, "away": ga},
                         "halftime": {"home": score_value(row.get("ht_home")), "away": score_value(row.get("ht_away"))}})
        stats = [
            {"teamId": hid, "statistics": match_stats(hid, aid, row, "home", stat_fields)},
            {"teamId": aid, "statistics": match_stats(hid, aid, row, "away", stat_fields)},
        ]
        if any(entry["statistics"] for entry in stats):
            fixture_stats[mid] = stats
    fixtures.sort(key=lambda f: f.get("date") or "")
    team_stats = team_statistics(fixtures)
    for tid, stats in team_stats.items():
        stats.update({"shots": 0, "corners": 0, "yellowCards": 0, "redCards": 0})
    for mid, stats in fixture_stats.items():
        for entry in stats:
            tid = entry["teamId"]
            for label, field in (("Shots", "shots"), ("Corners", "corners"), ("Yellow cards", "yellowCards"), ("Red cards", "redCards")):
                value = entry["statistics"].get(label)
                if value is not None:
                    team_stats.setdefault(tid, {}).setdefault(field, 0)
                    team_stats[tid][field] += int(value)
    standings_rows = standings(fixtures)
    snapshot = {"schemaVersion": 2, "competition": {"id": item["id"], "name": item["name"], "country": item.get("country")},
                "season": season_key, "seasonLabel": item["season"], "provider": "open-matchday (non-commercial use; attribution required)",
                "sourceUrl": "https://github.com/oladeeayo/open-matchday", "generatedAt": fetched_at,
                "fixtures": fixtures, "teams": list(teams.values()), "standings": standings_rows, "teamStats": team_stats,
                "fixtureStats": fixture_stats, "players": [], "topScorers": [],
                "coverage": {"fixtures": {"available": bool(fixtures), "rows": len(fixtures), "fetchedAt": fetched_at},
                             "standings": {"available": bool(standings_rows), "rows": len(standings_rows), "fetchedAt": fetched_at, "note": "Calculated from the source's completed match results."},
                             "teams": {"available": bool(teams), "rows": len(teams), "fetchedAt": fetched_at},
                             "players": {"available": False, "rows": 0, "note": "This source does not publish player season totals."},
                             "topScorers": {"available": False, "rows": 0, "note": "This source does not publish a player scorer table."},
                             "fixtureStats": {"available": bool(fixture_stats), "rows": len(fixture_stats), "fetchedAt": fetched_at}}}
    write_json(SNAPSHOTS / f"{item['id']}-{season_key}.json", snapshot)
    return snapshot


def normalize_cornerflick_ekstraklasa(item, season_key, fetched_at):
    source = fetch_json(CORNERFLICK_SEASON)
    source_updated = source.get("meta", {}).get("last_updated_at") or fetched_at
    fixtures, teams, fixture_stats, events, lineups = [], {}, {}, {}, {}
    goals_by_player = {}
    stats_rows = 0
    for match in source.get("matches", []):
        home_name, away_name = match.get("home_team"), match.get("away_team")
        if not home_name or not away_name:
            continue
        hid = f"cornerflick-team-{match.get('home_team_slug') or slug(home_name)}"
        aid = f"cornerflick-team-{match.get('away_team_slug') or slug(away_name)}"
        teams[hid] = {"id": hid, "name": home_name, "country": "Poland"}
        teams[aid] = {"id": aid, "name": away_name, "country": "Poland"}
        match_id = match.get("id", "")
        fid = f"cornerflick-{match.get('slug') or slug(match_id)}"
        kickoff = match.get("kickoff_at")
        finished = str(match.get("status", "")).lower() == "finished"
        fixtures.append({"id": fid, "date": kickoff, "timestamp": None, "round": match.get("round"), "status": "FT" if finished else "NS", "statusLong": "Finished" if finished else "Scheduled",
                         "home": {"id": hid, "name": home_name}, "away": {"id": aid, "name": away_name},
                         "goals": {"home": score_value(match.get("home_score")), "away": score_value(match.get("away_score"))},
                         "venue": match.get("venue"), "referee": match.get("referee"), "cornerflickUrl": match.get("url"), "cornerflickDataUrl": match.get("dataset_url")})
    fixture_by_data_url = {f.get("cornerflickDataUrl"): f for f in fixtures if f.get("cornerflickDataUrl")}
    urls = list(fixture_by_data_url)
    # Match details are cached into the static snapshot, so visitors do not need cross-site requests.
    from concurrent.futures import ThreadPoolExecutor
    def load_match(url):
        try:
            return url, fetch_json(url)
        except Exception as exc:
            print(f"Cornerflick match detail unavailable {url}: {exc}")
            return url, None
    with ThreadPoolExecutor(max_workers=8) as pool:
        for url, detail in pool.map(load_match, urls):
            if not detail:
                continue
            fixture = fixture_by_data_url[url]
            fid, home_id, away_id = fixture["id"], fixture["home"]["id"], fixture["away"]["id"]
            statistics = detail.get("statistics") or []
            if statistics:
                fixture_stats[fid] = [{"teamId": home_id, "statistics": {row["label"]: row.get("home") for row in statistics if row.get("home") is not None}},
                                      {"teamId": away_id, "statistics": {row["label"]: row.get("away") for row in statistics if row.get("away") is not None}}]
                stats_rows += 1
            events[fid] = [{"time": {"elapsed": ev.get("minute"), "extra": ev.get("extra")}, "team": ev.get("team"), "type": str(ev.get("type", "event")).replace("_", " ").title(), "detail": ev.get("detail", ""), "player": ev.get("player"), "assist": ev.get("assist")} for ev in detail.get("events", [])]
            lineup_data = detail.get("lineups") or {}
            lineups[fid] = [{"team": side_data.get("team", fixture["home"]["name"] if side == "home" else fixture["away"]["name"]), "formation": side_data.get("formation"), "coach": side_data.get("coach"),
                             "startXI": [{"name": p.get("name"), "position": p.get("position")} for p in side_data.get("starting_xi", [])],
                             "substitutes": [{"name": p.get("name"), "position": p.get("position")} for p in side_data.get("bench", [])]} for side, side_data in lineup_data.items()]
            for goal in detail.get("goals", []):
                name, team = goal.get("player"), goal.get("team")
                if not name:
                    continue
                key = slug(name)
                player = goals_by_player.setdefault(key, {"id": f"cornerflick-player-{key}", "name": name, "team": team, "goals": 0, "assists": 0})
                if goal.get("credited_side"):
                    player["goals"] += 1
                if goal.get("assist"):
                    assister_key = slug(goal["assist"])
                    assister = goals_by_player.setdefault(assister_key, {"id": f"cornerflick-player-{assister_key}", "name": goal["assist"], "team": team, "goals": 0, "assists": 0})
                    assister["assists"] += 1
    fixtures.sort(key=lambda f: f.get("date") or "")
    # Include forthcoming matchweeks from the no-key CSV feed, where the results source has not published fixtures yet.
    base = f"{OPEN_MATCHDAY}/POL_1_ekstraklasa"
    future_rows = fetch_csv(f"{base}/fixtures_2627.csv")
    def team_key(name):
        plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", "", plain)
    known = {(f["date"][:10] if f.get("date") else None, team_key(f["home"]["name"]), team_key(f["away"]["name"])) for f in fixtures}
    canonical_team_ids = {team_key(team["name"]): tid for tid, team in teams.items()}
    for row in future_rows:
        home, away = row.get("home", "").strip(), row.get("away", "").strip()
        if not home or not away or (row.get("date"), team_key(home), team_key(away)) in known:
            continue
        hid = canonical_team_ids.get(team_key(home), f"cornerflick-team-{slug(home)}")
        aid = canonical_team_ids.get(team_key(away), f"cornerflick-team-{slug(away)}")
        teams.setdefault(hid, {"id": hid, "name": home, "country": "Poland"}); teams.setdefault(aid, {"id": aid, "name": away, "country": "Poland"})
        fixtures.append({"id": f"openmatchday-ekstraklasa-{row.get('date')}-{slug(home)}-{slug(away)}", "date": row.get("date"), "round": f"Matchday {row.get('gw')}" if row.get("gw") else "", "status": "NS", "statusLong": "Scheduled", "home": {"id": hid, "name": home}, "away": {"id": aid, "name": away}, "goals": {"home": None, "away": None}})
    fixtures.sort(key=lambda f: f.get("date") or "")
    completed = [f for f in fixtures if f["status"] == "FT"]
    standings_rows = standings(completed)
    team_stats = team_statistics(completed)
    for fixture in fixtures:
        for team in (fixture["home"], fixture["away"]):
            if team["id"] not in team_stats:
                team_stats[team["id"]] = {"fixtures": {"played": 0, "wins": 0, "draws": 0, "loses": 0}, "goals": {"for": {"total": 0}, "against": {"total": 0}}, "clean_sheet": {"total": 0}}
    providers = "Cornerflick (CC BY 4.0) + open-matchday (non-commercial, attribution required)"
    snapshot = {"schemaVersion": 2, "competition": {"id": item["id"], "name": item["name"], "country": "Poland"}, "season": season_key, "seasonLabel": item["season"],
                "provider": providers, "sourceUrl": "https://cornerflick.com/data", "generatedAt": source.get("meta", {}).get("last_updated_at", fetched_at),
                "fixtures": fixtures, "teams": list(teams.values()), "standings": standings_rows, "teamStats": team_stats, "fixtureStats": fixture_stats,
                "events": events, "lineups": lineups, "players": sorted(goals_by_player.values(), key=lambda p: (-p["goals"], -p["assists"], p["name"])),
                "topScorers": sorted(goals_by_player.values(), key=lambda p: (-p["goals"], -p["assists"], p["name"]))[:100],
                "coverage": {"fixtures": {"available": bool(fixtures), "rows": len(fixtures), "fetchedAt": source_updated},
                             "standings": {"available": bool(standings_rows), "rows": len(standings_rows), "fetchedAt": source_updated, "note": "Calculated from completed Cornerflick results."},
                             "teams": {"available": bool(teams), "rows": len(teams), "fetchedAt": source_updated},
                             "players": {"available": bool(goals_by_player), "rows": len(goals_by_player), "note": "Season goals and assists aggregated from published match event records."},
                             "topScorers": {"available": bool(goals_by_player), "rows": min(len(goals_by_player), 100)},
                             "fixtureStats": {"available": bool(fixture_stats), "rows": stats_rows}, "events": {"available": bool(events), "rows": sum(len(x) for x in events.values())},
                             "lineups": {"available": bool(lineups), "rows": sum(len(x) for x in lineups.values())}}}
    write_json(SNAPSHOTS / f"{item['id']}-{season_key}.json", snapshot)
    return snapshot


def number(value, default=0):
    if value is None or str(value).strip() == "":
        return default
    try:
        if math.isnan(float(value)):
            return default
    except (TypeError, ValueError):
        pass
    return value


def sync_openplay(by_id, coverage):
    """Import licensed historical season aggregates from the OpenPlay release."""
    try:
        import duckdb
    except ImportError:
        coverage["openplay"] = {"available": False, "note": "DuckDB is not installed."}
        return
    request = urllib.request.Request(OPENPLAY_RELEASES, headers={"User-Agent": "football-stats-tracker/1.0", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        release = json.loads(response.read().decode("utf-8"))
    assets = {asset["name"]: asset["browser_download_url"] for asset in release.get("assets", [])}
    wanted = ("player_match_stats.parquet", "matches.parquet", "team_match_stats.parquet")
    missing = [name for name in wanted if name not in assets]
    if missing:
        coverage["openplay"] = {"available": False, "note": "Release missing: " + ", ".join(missing)}
        return
    with tempfile.TemporaryDirectory() as temp:
        paths = {}
        for name in wanted:
            path = Path(temp) / name
            req = urllib.request.Request(assets[name], headers={"User-Agent": "football-stats-tracker/1.0"})
            with urllib.request.urlopen(req, timeout=180) as response, path.open("wb") as output:
                output.write(response.read())
            paths[name] = str(path).replace("'", "''")
        con = duckdb.connect()
        players_path, matches_path, teams_path = (paths[name] for name in wanted)
        comp_rows = con.execute(f"SELECT DISTINCT comp, season FROM read_parquet('{players_path}')").fetchall()
        player_columns = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{players_path}')").fetchall()}
        sum_fields = [field for field in PLAYER_FIELDS if field in player_columns]
        for source_comp, source_season in comp_rows:
            comp_id = OPENPLAY_COMPS.get(str(source_comp).lower())
            item = by_id.get(comp_id)
            if not item:
                continue
            code = str(source_season)
            if source_comp in {"eng", "esp", "ita", "ger", "fra", "ucl", "uel", "nla", "nlb"} and len(code) == 4 and code.isdigit():
                season_key, label = "20" + code[:2], f"20{code[:2]}/{code[2:]}"
            else:
                season_key = code
                label = code if len(code) == 4 else code
            existing_path = SNAPSHOTS / f"{comp_id}-{season_key}.json"
            existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else None
            where = f"comp = '{str(source_comp).replace(chr(39), chr(39)*2)}' AND season = '{code}'"
            expressions = [f"sum({field}) AS {field}" for field in sum_fields]
            grouping = ", ".join(["player_id", "player", "team_id", "team", "position"])
            query = f"SELECT {grouping}, count(*) FILTER (WHERE played) AS appearances, sum(minutes_played) AS minutes, {', '.join(expressions)} FROM read_parquet('{players_path}') WHERE {where} GROUP BY {grouping}"
            player_rows = con.execute(query).fetchdf().to_dict("records")
            players_out = []
            for p in player_rows:
                row = {"id": f"op-player-{p['player_id']}", "name": p["player"], "team": p["team"], "teamId": f"op-team-{p['team_id']}", "position": p["position"], "appearances": int(number(p["appearances"])), "minutes": int(number(p["minutes"]))}
                for field in sum_fields:
                    value = p[field]
                    if number(value, None) is not None:
                        value = number(value)
                        mapped = {"shots_on_target":"shotsOnTarget", "shots_off_target":"shotsOffTarget", "shots_blocked":"shotsBlocked", "key_passes":"keyPasses", "passes_completed":"passesCompleted", "passes_final_third":"passesFinalThird", "passes_into_box":"passesIntoBox", "dribbles_completed":"dribblesCompleted", "tackles_won":"tacklesWon", "ball_recoveries":"ballRecoveries", "yellow_cards":"yellowCards", "second_yellows":"secondYellows", "red_cards":"redCards"}.get(field, field)
                        row[mapped] = round(float(value), 2) if field in ("xg", "npxg", "xa") else int(value)
                row.update({"expectedGoals": row.get("xg"), "expectedAssists": row.get("xa")})
                players_out.append(row)
            players_out.sort(key=lambda p: (-p.get("goals", 0), -p.get("assists", 0), str(p.get("name") or "")))
            match_rows = con.execute(f"SELECT * FROM read_parquet('{matches_path}') WHERE {where} ORDER BY date").fetchdf().to_dict("records")
            fixtures, team_names, standings_rows = [], {}, []
            for m in match_rows:
                hid, aid = f"op-team-{m['home_team_id']}", f"op-team-{m['away_team_id']}"
                hn, an = m["home_team"], m["away_team"]
                team_names[hid], team_names[aid] = hn, an
                fixtures.append({"id": f"openplay-{m['match_id']}", "openplayMatchId": int(m["match_id"]), "date": str(m["date"]), "round": str(m.get("round") or ""), "status": "FT", "statusLong": "Finished", "home": {"id": hid, "name": hn}, "away": {"id": aid, "name": an}, "goals": {"home": int(m["home_score"]), "away": int(m["away_score"])}})
            team_columns = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{teams_path}')").fetchall()}
            available_team_fields = [field for field in ("shots", "shots_on_target", "passes", "passes_completed", "key_passes", "assists", "xg", "npxg", "tackles", "interceptions", "clearances", "saves", "yellow_cards", "red_cards") if field in team_columns]
            team_sums = ", ".join(["team_id"] + [f"sum({field}) AS {field}" for field in available_team_fields] + ["sum(goals_for) AS goals_for", "sum(goals_against) AS goals_against", "count(*) AS matches"])
            team_stats = {}
            for t in con.execute(f"SELECT {team_sums} FROM read_parquet('{teams_path}') WHERE {where} GROUP BY team_id").fetchdf().to_dict("records"):
                tid = f"op-team-{t['team_id']}"
                team_stats[tid] = {"fixtures": {"played": int(number(t["matches"]))}, "goals": {"for": {"total": int(number(t["goals_for"]))}, "against": {"total": int(number(t["goals_against"]))}}, "shots": int(number(t.get("shots"))), "xg": round(float(number(t.get("xg"))), 2), "passes": int(number(t.get("passes"))), "tackles": int(number(t.get("tackles"))), "interceptions": int(number(t.get("interceptions")))}
            match_team_fields = [field for field in ("shots", "shots_on_target", "passes", "passes_completed", "key_passes", "assists", "xg", "npxg", "tackles", "interceptions", "clearances", "saves", "yellow_cards", "red_cards", "corners_taken") if field in team_columns]
            match_stats = {}
            select_match = ", ".join(["match_id", "team_id"] + match_team_fields)
            for t in con.execute(f"SELECT {select_match} FROM read_parquet('{teams_path}') WHERE {where}").fetchdf().to_dict("records"):
                mid, tid = f"openplay-{t['match_id']}", f"op-team-{t['team_id']}"
                labels = {"shots":"Shots", "shots_on_target":"Shots on target", "passes":"Passes", "passes_completed":"Passes completed", "key_passes":"Key passes", "assists":"Assists", "xg":"xG", "npxg":"Non-penalty xG", "tackles":"Tackles", "interceptions":"Interceptions", "clearances":"Clearances", "saves":"Saves", "yellow_cards":"Yellow cards", "red_cards":"Red cards", "corners_taken":"Corners"}
                match_stats.setdefault(mid, []).append({"teamId": tid, "statistics": {labels[field]: round(float(number(t[field])), 2) if field in ("xg", "npxg") else int(number(t[field])) for field in match_team_fields}})
            if comp_id in {"premier-league", "la-liga", "serie-a", "bundesliga", "ligue-1"}:
                standings_rows = standings(fixtures)
            teams_out = [{"id": tid, "name": name} for tid, name in sorted(team_names.items(), key=lambda x: x[1])]
            merged_fixtures = fixtures
            if existing:
                keys = {(f["date"], f["home"]["name"], f["away"]["name"]) for f in fixtures}
                merged_fixtures = [f for f in existing.get("fixtures", []) if (f.get("date"), f.get("home",{}).get("name"), f.get("away",{}).get("name")) not in keys] + fixtures
            snapshot = existing or {"schemaVersion": 2, "competition": {"id": comp_id, "name": item["name"], "country": item.get("country")}, "season": season_key, "seasonLabel": label, "standings": [], "fixtureStats": {}, "events": {}, "lineups": {}}
            snapshot.update({"seasonLabel": label, "provider": "OpenPlay (CC BY 4.0)" + (" + StatsBomb Open Data" if existing and existing.get("provider")=="StatsBomb Open Data" else ""), "sourceUrl": "https://github.com/nlbair/openplay", "generatedAt": release.get("tag_name", "OpenPlay release"), "fixtures": merged_fixtures, "teams": teams_out, "players": players_out, "topScorers": players_out[:100], "teamStats": {**(existing or {}).get("teamStats", {}), **team_stats}, "fixtureStats": {**(existing or {}).get("fixtureStats", {}), **match_stats}, "standings": standings_rows or (existing or {}).get("standings", [])})
            rows = {"fixtures": len(fixtures), "players": len(players_out), "teams": len(teams_out)}
            snapshot.setdefault("coverage", {}).update({key: {"available": True, "rows": value, "note": "OpenPlay historical snapshot; not live."} for key, value in rows.items()})
            snapshot["coverage"]["topScorers"] = {"available": True, "rows": min(len(players_out), 100), "note": "Ranked by goals from OpenPlay player match totals."}
            write_json(existing_path, snapshot)
            row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
            row["seasons"].append(season_key)
            openplay_state = row.setdefault("openplay", {"available": True, "rows": 0, "players": 0, "version": release.get("tag_name"), "seasons": []})
            openplay_state["rows"] += len(fixtures)
            openplay_state["players"] += len(players_out)
            openplay_state["seasons"].append(label)
            row.setdefault("seasonLabels", {})[season_key] = label
            for key in ("fixtures", "players", "teams", "topScorers"):
                row[key] = snapshot["coverage"][key]
            if standings_rows:
                row["standings"] = {"available": True, "rows": len(standings_rows), "note": "Calculated from available OpenPlay match results; a small number of source gaps may remain."}
        coverage["openplay"] = {"available": True, "version": release.get("tag_name"), "competitions": len(OPENPLAY_COMPS), "license": "CC BY 4.0"}
        con.close()


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


def score_value(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
        score = row.get("score")
        if isinstance(score, list):
            # OpenFootball files use a two-item score for full-time-only results.
            ft, ht = score, [None, None]
        elif isinstance(score, dict):
            ft, ht = score.get("ft") or [None, None], score.get("ht") or [None, None]
        else:
            ft, ht = [None, None], [None, None]
        ft_home = score_value(ft[0]) if len(ft) >= 2 else None
        ft_away = score_value(ft[1]) if len(ft) >= 2 else None
        ht_home = score_value(ht[0]) if len(ht) >= 2 else None
        ht_away = score_value(ht[1]) if len(ht) >= 2 else None
        played = ft_home is not None and ft_away is not None
        fixtures.append({
            "id": f"openfootball-{item['id']}-{index}", "date": row.get("date"), "timestamp": None,
            "round": row.get("round"), "status": "FT" if played else "NS", "statusLong": "Finished" if played else "Scheduled",
            "home": {"id": home_id, "name": home_name}, "away": {"id": away_id, "name": away_name},
            "goals": {"home": ft_home if played else None, "away": ft_away if played else None},
            "halftime": {"home": ht_home, "away": ht_away},
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
    coverage = {"schemaVersion": 2, "provider": "OpenFootball + StatsBomb + OpenPlay + open-matchday + Cornerflick", "status": "partial", "generatedAt": fetched_at,
                "sources": [{"name": "OpenFootball", "url": "https://github.com/openfootball/football.json", "license": "CC0-1.0"},
                            {"name": "StatsBomb Open Data", "url": "https://github.com/hudl/open-data", "license": "Attribution required"},
                            {"name": "OpenPlay", "url": "https://github.com/nlbair/openplay", "license": "CC BY 4.0 · credit Noah Bair / openplay"},
                            {"name": "open-matchday", "url": "https://github.com/oladeeayo/open-matchday", "license": "Non-commercial use only; attribution required"},
                            {"name": "Cornerflick", "url": "https://cornerflick.com/data", "license": "CC BY 4.0 · attribution: Data by Cornerflick — cornerflick.com"}],
                "competitions": {}, "message": "Static open datasets; current fixtures and results include OpenFootball and open-matchday coverage. Ekstraklasa includes Cornerflick match reports, events, lineups and stats. Historical event data is available for selected StatsBomb seasons. Other sections stay unavailable where no open file source covers them."}
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
            row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
            row["openfootball"] = {"available": False, "note": f"OpenFootball file could not be refreshed: {exc}"}
            print(f"OpenFootball {comp_id}: {exc}")
    for comp_id, folder in (("premier-league", "ENG_1_premier-league"), ("ekstraklasa", "POL_1_ekstraklasa")):
        item = by_id.get(comp_id)
        if not item:
            continue
        try:
            snap = normalize_openmatchday(item, "2026", folder, fetched_at)
            row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
            row["seasons"].append("2026")
            row.setdefault("seasonLabels", {})["2026"] = item["season"]
            row["openmatchday"] = {"available": True, "rows": len(snap["fixtures"]), "fetchedAt": fetched_at}
            for section, state in snap["coverage"].items():
                if state.get("available"):
                    row[section] = state
        except Exception as exc:
            coverage["competitions"].setdefault(comp_id, {"seasons": []})["openmatchday"] = {"available": False, "note": str(exc)}
            print(f"open-matchday {comp_id}: {exc}")
    item = by_id.get("ekstraklasa")
    if item:
        try:
            snap = normalize_cornerflick_ekstraklasa(item, "2026", fetched_at)
            row = coverage["competitions"].setdefault("ekstraklasa", {"seasons": []})
            row["seasons"].append("2026")
            row.setdefault("seasonLabels", {})["2026"] = item["season"]
            row["cornerflick"] = {"available": True, "rows": len(snap["fixtures"]), "completed": sum(f["status"] == "FT" for f in snap["fixtures"]), "detailedMatches": len(snap["fixtureStats"]), "fetchedAt": snap["generatedAt"]}
            for section, state in snap["coverage"].items():
                if state.get("available"):
                    row[section] = state
        except Exception as exc:
            coverage["competitions"].setdefault("ekstraklasa", {"seasons": []})["cornerflick"] = {"available": False, "note": str(exc)}
            print(f"Cornerflick Ekstraklasa: {exc}")
    for comp_id, seasons in STATSBOMB_SEASONS.items():
        item = by_id.get(comp_id)
        if not item:
            continue
        for source_comp, source_season, label, season_key in seasons:
            try:
                snap = normalize_statsbomb(item, source_comp, source_season, label, season_key, fetched_at)
                row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
                row["seasons"].append(season_key)
                row.setdefault("seasonLabels", {})[season_key] = label
                for section, state in snap["coverage"].items():
                    if state.get("available"):
                        row.setdefault(section, state)
                statsbomb = row.setdefault("statsbomb", {"available": True, "rows": 0, "fetchedAt": fetched_at, "seasons": []})
                statsbomb["rows"] += len(snap["fixtures"])
                statsbomb["seasons"].append(label)
            except Exception as exc:
                coverage["competitions"].setdefault(comp_id, {"seasons": []})["statsbomb"] = {"available": False, "note": f"StatsBomb match list unavailable: {exc}"}
    try:
        sync_openplay(by_id, coverage)
    except Exception as exc:
        coverage["openplay"] = {"available": False, "note": f"OpenPlay download failed: {exc}"}
        print(f"OpenPlay: {exc}")
    for row in coverage["competitions"].values():
        row["seasons"] = sorted(set(row.get("seasons", [])), reverse=True)
    write_json(DATA / "coverage.json", coverage)
    print(json.dumps({"sources": 3, "competitions_with_files": len(coverage["competitions"]), "status": coverage["status"]}, indent=2))


if __name__ == "__main__":
    main()
