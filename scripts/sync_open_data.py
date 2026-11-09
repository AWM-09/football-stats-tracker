#!/usr/bin/env python3
"""Refresh static, openly published football datasets; no API key is used."""
from __future__ import annotations

import datetime as dt
import json
import re
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SNAPSHOTS = DATA / "competitions"
OPENFOOTBALL = "https://raw.githubusercontent.com/openfootball/football.json/master"
STATSBOMB = "https://raw.githubusercontent.com/hudl/open-data/master/data"
OPENPLAY_RELEASES = "https://api.github.com/repos/nlbair/openplay/releases/latest"
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
            if len(code) == 4 and code.isdigit() and int(code[:2]) >= 10:
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
                row = {"id": f"op-player-{p['player_id']}", "name": p["player"], "team": p["team"], "teamId": f"op-team-{p['team_id']}", "position": p["position"], "appearances": int(p["appearances"] or 0), "minutes": int(p["minutes"] or 0)}
                for field in sum_fields:
                    value = p[field]
                    if value is not None:
                        mapped = {"shots_on_target":"shotsOnTarget", "shots_off_target":"shotsOffTarget", "shots_blocked":"shotsBlocked", "key_passes":"keyPasses", "passes_completed":"passesCompleted", "passes_final_third":"passesFinalThird", "passes_into_box":"passesIntoBox", "dribbles_completed":"dribblesCompleted", "tackles_won":"tacklesWon", "ball_recoveries":"ballRecoveries", "yellow_cards":"yellowCards", "second_yellows":"secondYellows", "red_cards":"redCards"}.get(field, field)
                        row[mapped] = round(float(value), 2) if field in ("xg", "npxg", "xa") else int(value)
                row.update({"expectedGoals": row.get("xg"), "expectedAssists": row.get("xa")})
                players_out.append(row)
            players_out.sort(key=lambda p: (-p.get("goals", 0), -p.get("assists", 0), p["name"]))
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
                team_stats[tid] = {"fixtures": {"played": int(t["matches"] or 0)}, "goals": {"for": {"total": int(t["goals_for"] or 0)}, "against": {"total": int(t["goals_against"] or 0)}}, "shots": int(t.get("shots") or 0), "xg": round(float(t.get("xg") or 0), 2), "passes": int(t.get("passes") or 0), "tackles": int(t.get("tackles") or 0), "interceptions": int(t.get("interceptions") or 0)}
            match_team_fields = [field for field in ("shots", "shots_on_target", "passes", "passes_completed", "key_passes", "assists", "xg", "npxg", "tackles", "interceptions", "clearances", "saves", "yellow_cards", "red_cards", "corners_taken") if field in team_columns]
            match_stats = {}
            select_match = ", ".join(["match_id", "team_id"] + match_team_fields)
            for t in con.execute(f"SELECT {select_match} FROM read_parquet('{teams_path}') WHERE {where}").fetchdf().to_dict("records"):
                mid, tid = f"openplay-{t['match_id']}", f"op-team-{t['team_id']}"
                labels = {"shots":"Shots", "shots_on_target":"Shots on target", "passes":"Passes", "passes_completed":"Passes completed", "key_passes":"Key passes", "assists":"Assists", "xg":"xG", "npxg":"Non-penalty xG", "tackles":"Tackles", "interceptions":"Interceptions", "clearances":"Clearances", "saves":"Saves", "yellow_cards":"Yellow cards", "red_cards":"Red cards", "corners_taken":"Corners"}
                match_stats.setdefault(mid, []).append({"teamId": tid, "statistics": {labels[field]: round(float(t[field]), 2) if field in ("xg", "npxg") and t[field] is not None else (int(t[field]) if t[field] is not None else 0) for field in match_team_fields}})
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
            row["openplay"] = {"available": True, "rows": len(fixtures), "players": len(players_out), "version": release.get("tag_name"), "season": label}
            for key in ("fixtures", "players", "teams", "topScorers"):
                row[key] = snapshot["coverage"][key]
            if standings_rows:
                row["standings"] = {"available": True, "rows": len(standings_rows), "note": "Calculated from complete OpenPlay league results."}
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
    coverage = {"schemaVersion": 2, "provider": "OpenFootball + StatsBomb + OpenPlay", "status": "partial", "generatedAt": fetched_at,
                "sources": [{"name": "OpenFootball", "url": "https://github.com/openfootball/football.json", "license": "CC0-1.0"},
                            {"name": "StatsBomb Open Data", "url": "https://github.com/hudl/open-data", "license": "Attribution required"},
                            {"name": "OpenPlay", "url": "https://github.com/nlbair/openplay", "license": "CC BY 4.0 · credit Noah Bair / openplay"}],
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
            row = coverage["competitions"].setdefault(comp_id, {"seasons": []})
            row["openfootball"] = {"available": False, "note": f"OpenFootball file could not be refreshed: {exc}"}
            print(f"OpenFootball {comp_id}: {exc}")
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
