# Football & Soccer Stats Tracker

A static football statistics site in the AlexMyrusTalksSports family. The home page groups competitions into selectable cards; each competition hub includes season selection and sections for tables, fixtures, teams, players, head-to-head and records.

## Competition directory

The directory lists six top-flight leagues, UEFA club competitions, international tournaments, and domestic cups from England and Poland only. A listed competition is not a promise of data coverage: the open datasets cover only selected competitions and seasons. The Data Status page shows exact coverage.

## Free, keyless data

The daily GitHub Actions workflow downloads public JSON files from:

- [OpenFootball](https://github.com/openfootball/football.json), licensed CC0-1.0. The current feed is limited to the five configured top-flight leagues. Fixtures and results are published; standings are calculated from completed scores. This source does not provide player statistics.
- [StatsBomb Open Data](https://github.com/hudl/open-data), which publishes event data for selected historical competitions and seasons. Supported match pages can show shots, xG, cards, events and lineups. StatsBomb requires attribution when sharing analysis; the site links and credits the source.
- [OpenPlay](https://github.com/nlbair/openplay), a CC BY 4.0 snapshot with player and team match totals, xG/xA, shots, passing, defending and match results across the five major European leagues, UEFA competitions and selected international tournaments. The workflow imports season summaries; attribution is provided on the Data Status page.
- [open-matchday](https://github.com/oladeeayo/open-matchday) supplies 2026/27 fixtures, results, goal events and selected match statistics for the five major leagues, UEFA Champions/Europa/Conference Leagues, and English FA/EFL Cups. Its terms restrict use to non-commercial projects and require attribution.
- [Cornerflick](https://cornerflick.com/data) supplies Ekstraklasa results, match statistics, event timelines and lineups under CC BY 4.0. The site credits Cornerflick.

There is no API key or paid service. Data is not live. OpenPlay currently covers historical seasons through 2025/26; GitHub Actions refreshes supported current-season snapshots once per day. The five major leagues, UEFA club competitions and English cups use the 2026/27 season. Ekstraklasa is labeled 2026/27; calendar-year international tournaments retain their actual year. Polish domestic cups stay in the directory but these feeds do not publish their current-season data. Check each provider's terms before reusing its data, especially open-matchday's non-commercial restriction. Unsupported sections and seasons are labeled unavailable rather than filled with estimates.

## Local preview

Serve this folder with any static file server. No build step or credentials are needed. The workflow can also be run manually from the GitHub Actions tab.

## Pages

- `index.html` — competition directory.
- `competition.html?id=...` — competition hub and season data.
- `stats.html?competition=...&season=...` — soccer stats tracker with matchweek filters, player and team leaderboards, totals, trends and comparisons.
- `entity.html?type=team|player&id=...` — team or player profile where source data exists.
- `match.html?id=...` — match stats, events and lineups for supported matches.
- `health.html` — source notes and per-competition coverage.
- `scripts/sync_open_data.py` — fetch and normalize public data files.
