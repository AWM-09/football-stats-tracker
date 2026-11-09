# Football & Soccer Stats Tracker

A static football statistics site in the AlexMyrusTalksSports family. The home page groups competitions into selectable cards; each competition hub includes season selection and sections for tables, fixtures, teams, players, head-to-head and records.

## Competition directory

The directory lists six top-flight leagues, UEFA club competitions, international tournaments and domestic cups. A listed competition is not a promise of data coverage: the open datasets cover only selected competitions and seasons. The Data Status page shows exact coverage.

## Free, keyless data

The daily GitHub Actions workflow downloads public JSON files from:

- [OpenFootball](https://github.com/openfootball/football.json), licensed CC0-1.0. The current feed is limited to the five configured top-flight leagues. Fixtures and results are published; standings are calculated from completed scores. This source does not provide player statistics.
- [StatsBomb Open Data](https://github.com/hudl/open-data), which publishes event data for selected historical competitions and seasons. Supported match pages can show shots, xG, cards, events and lineups. StatsBomb requires attribution when sharing analysis; the site links and credits the source.

There is no API key or paid service. Data is not live; the workflow refreshes once per day. This does not provide full current-season coverage across all 35 competitions, complete player season totals, transfers or live scores. Unsupported sections and seasons are labeled unavailable rather than filled with estimates. Standings derived from partial or knockout schedules are not shown as league tables.

## Local preview

Serve this folder with any static file server. No build step or credentials are needed. The workflow can also be run manually from the GitHub Actions tab.

## Pages

- `index.html` — competition directory.
- `competition.html?id=...` — competition hub and season data.
- `entity.html?type=team|player&id=...` — team or player profile where source data exists.
- `match.html?id=...` — match stats, events and lineups for supported matches.
- `health.html` — source notes and per-competition coverage.
- `scripts/sync_open_data.py` — fetch and normalize public data files.
