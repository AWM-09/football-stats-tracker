# Football & Soccer Stats Tracker

An independent football statistics project in the AlexMyrusTalksSports family. The competition directory follows the card-based home page used by the NFL tracker, with a dedicated hub route for each competition.

## Competition directory

- **Leagues:** Premier League, Ligue 1, La Liga, Serie A, Bundesliga and Ekstraklasa.
- **UEFA club competitions:** Champions League, Europa League and Conference League.
- **International football:** FIFA World Cup, UEFA European Championship, UEFA Nations League, World Cup qualifiers, Copa América, Africa Cup of Nations, AFC Asian Cup and CONCACAF Gold Cup.
- **Domestic cups:** FA Cup, EFL Cup, Community Shield, Coupe de France, Trophée des Champions, Copa del Rey, Supercopa de España, Coppa Italia, Supercoppa Italiana, DFB-Pokal, DFL-Supercup, Puchar Polski and Superpuchar Polski.

The catalogue is searchable and filterable. Competition links open a hub with sections planned for overview, standings, fixtures and results, teams, players and records.

## Data status

The repository currently has no football data provider configured. It does not display sample scores, fabricated tables or unverified statistics. Each competition hub and the Data Status page say when data is unavailable.

API-Football is a possible single-provider fit: its coverage page currently lists 1,251 leagues and cups, while its free plan advertises 100 requests per day and limits available seasons. Competition-by-competition depth can vary. Review its [current plan](https://www.api-football.com/pricing) and [coverage](https://www.api-football.com/coverage) before connecting it. The API key must stay on the server side (for example, in a GitHub Actions secret); never put it in browser JavaScript or commit it to this repository.

## Planned data model

Store normalized, dated snapshots keyed by stable provider IDs:

- Competition and season metadata.
- Clubs, national teams and season rosters.
- Fixtures, scores, match events and standings.
- Player appearances and season totals, including goals, assists and clean sheets.
- Advanced fields such as xG only when the source supplies them for that competition and season.
- Transfer history, suspensions, honours and records when coverage is verified.

Every published dataset should include its provider, source season, fetched timestamp, coverage notes and validation result. Missing fields should stay missing rather than being inferred as zero.

## Local preview

Open `index.html` directly, or serve this folder with any static file server. No build step or API credentials are needed for the competition directory.

## Pages

- `index.html` — competition directory.
- `competition.html?id=...` — competition hub scaffold.
- `health.html` — current data connection and coverage status.
