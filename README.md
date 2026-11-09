# Football & Soccer Stats Tracker

An independent football statistics project in the AlexMyrusTalksSports family. Its card based home page opens competition hubs with season selectors and sections for standings, fixtures, teams, players, head to head and records.

## Competition directory

- **Leagues:** Premier League, Ligue 1, La Liga, Serie A, Bundesliga and Ekstraklasa.
- **UEFA club competitions:** Champions League, Europa League and Conference League.
- **International football:** FIFA World Cup, UEFA European Championship, UEFA Nations League, regional World Cup qualifiers, Copa América, Africa Cup of Nations, AFC Asian Cup and CONCACAF Gold Cup.
- **Domestic cups:** FA Cup, EFL Cup, Community Shield, Coupe de France, Trophée des Champions, Copa del Rey, Supercopa de España, Coppa Italia, Supercoppa Italiana, DFB-Pokal, DFL-Supercup, Puchar Polski and Superpuchar Polski.

## Stats and data connection

Competition snapshots can include tables, fixtures and scores, team lists and season statistics, player appearances and metrics, top scorers, match statistics, events and lineups. Each competition and section records its own source coverage and fetch time. Data is shown only when received from the provider; missing values are not treated as zero. xG, transfers, suspensions, honours and other fields are not implied when the source does not provide them.

The site is built and published, but live football data remains unavailable until an API-Football key is configured. In the GitHub repository, open **Settings → Secrets and variables → Actions**, add secret `API_FOOTBALL_KEY`, then run **Deploy Football Stats Tracker** in Actions. The secret stays in the workflow and is never sent to the browser. The workflow rotates across data groups and writes dated snapshots to the repository. Team and per-match statistics take multiple provider calls, so full coverage across all competitions takes time and depends on plan limits.

The provider currently lists 1,251 leagues and cups, with coverage depth varying by competition and season. Review [current pricing](https://www.api-football.com/pricing) and [coverage](https://www.api-football.com/coverage) before choosing an API plan. The sync defaults to a 90-request daily budget.

## Local preview

Serve this folder with any static file server. No build step or API credentials are needed to preview the site. Without snapshots the pages show explicit unavailable states.

## Pages

- `index.html` — competition directory.
- `competition.html?id=...` — competition data and analysis hub.
- `entity.html?type=team|player&id=...` — team and player season profiles.
- `match.html?id=...` — match statistics, events and lineups.
- `health.html` — provider setup and per competition data coverage.
