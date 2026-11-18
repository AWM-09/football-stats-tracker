# Football / Soccer

The site is in a layout-first rebuild. The first page is a competition directory. Each competition opens a dashboard with the planned page sections and tools.

## Layout phase

No scores, player totals, standings, predictions, records, or data-driven tables are shown on the website. The page templates use visual placeholders so the navigation, hierarchy, and responsive layouts can be settled before statistics are reintroduced.

The original data snapshots and import scripts remain in the repository for a later phase, but the Pages workflow no longer publishes them or runs the statistics refresh. The published site includes only the competition catalogue needed to populate the directory.

## Pages

- `index.html` — competition directory
- `competition.html` — competition dashboard and section previews
- `stats.html`, `advanced.html`, `research.html`, `records`, `weekly.html`, `accuracy.html` — statistics and analysis page layouts
- `calendar.html`, `match.html` — match centre layouts
- `entity.html` — player and team profile layout
- `favorites.html`, `news.html`, `commentary.html`, `playbook.html`, `rulebook.html`, `health.html` — fan and reference page layouts

## Local preview

Serve this folder with any static file server. No build step or credentials are needed. GitHub Actions publishes the layout to GitHub Pages on pushes to `main` or a manual workflow run.
