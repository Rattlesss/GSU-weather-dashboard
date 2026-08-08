## July 8, 2026

#### environment & project setup

- Set up GitHub repo (GSU-weather-dashboard), connected local PyCharm project
- Created project folder structure (src/, dashboard/, data/raw/)
- Set up Python virtualenv, installed requests, pandas, sqlalchemy, pymysql,
  streamlit, plotly, python-dotenv; froze requirements.txt
- Installed MariaDB locally via Homebrew, created weather_project database
- Created .env for DB credentials (git-ignored)
- Point of interest: Georgia Southern University, Statesboro campus
  (lat 32.4194, lon -81.7767), located in Bulloch County, GA
- Tested NASA POWER API for full year 2025 (T2M, PRECTOTCORR) — confirmed
  200 response with real daily data
- Early observation: API returns data nested by parameter then by date
  (not row-per-date); will need reshaping in clean_data.py. Data source
  is MERRA2 (reanalysis model, not direct station observations).

#### schema design

- Decided to expand beyond original 2 variables (temperature, precipitation)
  to 6 total: T2M, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PS
- Designed and created schema.sql: single table `daily_weather`, one row
  per date, date as PRIMARY KEY (no separate location table needed since
  this project tracks a single point)
- Used DECIMAL(5,2)/(6,2) for numeric columns, sized based on realistic
  ranges seen in the test API pull
- Added inline COMMENT metadata on each column documenting the source
  variable name and units (visible via SHOW FULL COLUMNS)
- Ran schema.sql against local MariaDB, confirmed table created correctly
  with all 7 columns (date + 6 variables) and comments intact
- Learned: schema/column changes don't require code changes elsewhere yet
  since no data has been loaded; safe to iterate on schema early

#### db.py, fetch_data.py, clean_data.py

- Built db.py: loads DB credentials from .env using python-dotenv, builds
  a SQLAlchemy connection string, creates a reusable engine object.
  Tested successful connection to weather_project database.
- Built fetch_data.py: wrapped the NASA POWER API call in a reusable
  function (fetch_weather_data) taking start/end date arguments, requesting
  all 6 variables at once. Added raise_for_status() so failed requests
  raise a clear error instead of failing silently.
- Built clean_data.py: reshapes the API's nested JSON (parameter -> date ->
  value) into a flat table, one row per date. Converts date strings to
  real datetime objects, renames API variable names to match schema.sql
  column names, replaces NASA's -999 missing-value code with NaN.
- Verified: 365 rows x 7 columns for full year 2025, matches expected shape.
- Bugs caught along the way: case-sensitive JSON key typo (Parameter vs
  parameter), typo in column rename mapping (ALLSHY vs ALLSKY), wrong
  missing-value placeholder (-99 vs -999).

#### load_data.py, full pipeline working

- Built load_data.py: loads cleaned DataFrame into daily_weather using
  REPLACE INTO with named parameters (safe against SQL injection, and
  re-runnable without creating duplicate rows for the same date).
- Ran full pipeline end-to-end for the first time: fetch_data -> clean_data
  -> load_data. Confirmed 365 rows loaded into MariaDB.
- Bugs caught: missing VALUES clause in first draft, repeated column-name
  mismatch (kwh2 vs kwhm2) between SQL and Python dict keys.
- Milestone: full data pipeline (API -> clean -> DB) is functional.
-Verified in MariaDB directly: SELECT COUNT(*) returned 365, spot-checked
  first 5 rows, values look correct across all 6 variables.

#### dashboard build

- Built dashboard/app.py: Streamlit dashboard with sidebar date filter,
  summary metric cards (hottest/coldest/wettest day, avg humidity),
  tabbed layout across 3 sections, and a correlation heatmap
- Added axis constraints (minallowed/maxallowed) so panning/zooming can't
  drift past the actual data range
- Wrote README.md with setup instructions and an honest note on AI use
- Project complete: full pipeline (fetch -> clean -> load) plus
  interactive dashboard, matching original Day 1 plan



## August 3, 2026

#### docker-compose.yml

- Added MariaDB 11 service, containerized with a named volume
    (mariadb_data) so data persists across container restarts
- Mounted src/schema.sql as the init script - daily_weather table
    gets created automatically on first container boot, no manual
    setup needed
- Exposed on host port 3307 (not 3306) to avoid clashing with any
    local native MariaDB install
- Added a healthcheck (--connect --innodb_initialized) so readiness
    can be checked before the app or a script tries to connect
    
#### .env.example

- Added a template documenting the required env vars
    (DB_ROOT_PASSWORD, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST,
    DB_PORT) with no real secrets, so the repo is cloneable without
    guessing at what .env needs to contain
    
#### bug: user creation silently failing

- MARAIDB_PASSWORD typo (should be MARIADB_PASSWORD) in the
    environment block meant MARIADB_USER had no valid password to
    pair with - container started fine and created the database, but
    never created the weather_app user
- Caught by comparing docker-compose logs db output against a
    working MariaDB entrypoint log - the "Creating user weather_app"
    line was simply missing
- Fixed the key name, wiped the volume (docker-compose down -v),
    and reinitialized clean
    
#### verification

- Brought the container up with docker-compose up -d, confirmed
    status reached healthy
- Connected via mycli as the scoped weather_app user (not root) -
    confirmed via docker exec ... env that MARIADB_USER/PASSWORD
    matched what mycli was being given
- Ran SHOW TABLES / DESCRIBE daily_weather - confirmed all 7
    columns present and matching schema.sql, primary key intact on
    date
- Merged feature/docker-support into main via PR after verification

## August 8, 2026

#### Personal Dev Explanation

- Before we get into the devlog for today, I have some explaining to do.
- Installed / Configured a new Fedora KDE Plasma system today, 
has all the same dev features as my MacOS setup!
- Pulled the entire project from the Github repo, 
first time ever doing it that way. Before today, I could do 
everything locally on my trusty Macbook Neo.
- The setup from repo process blows currently. Doing the config is just awful.
- Also learned the code is wildly unoptimized. It seemed to be pulling API
requests TWICE at runtime. Once during the fetch phase (as it should), 
and then AGAIN at the load phase. Why??
- I had to fix that. I can't just overlook both an awful setup process and
bad code. That just ain't right. So thats what I did today. It's 1am. I wanna go to bed.
- If you're an end user who tried to use my DB/Dashboard before this, I'm so sorry. 
- So very sorry.

#### terminal logging (fetch_data.py)
- Replaced messy print() calls with Python's built-in logging module -
  logging.basicConfig() configured once at the top of the file (level
  INFO, timestamp + level + message format, HH:MM:SS timestamps)
- logger = logging.getLogger(__name__) used instead of the root logger
  directly, so log output is scoped to this module rather than global
- Logged each meaningful step of the year-by-year fetch loop: start of
  the whole range fetch (with year count), each year being requested,
  how many days came back per year, and the sleep between requests -
  gives a live progress trail during the ~34-60s multi-year fetch
  instead of a silent wait
- Chose logging over print() specifically because it timestamps every
  line automatically and can have its verbosity level adjusted later
  without touching each call site individually
- This is exactly how I figured out that the code was making 
multiple API pulls. It's always great when a simple QoL change
ends up costing you multiple hours.
- Maybe this is the end of QoL changes? Who knows.

#### run_pipeline.py

- Added a single orchestrator script (fetch -> clean -> save CSV -> load)
  after realizing fetch_data.py and load_data.py's __main__ blocks each
  independently called the fetch function - meant NASA's API was being
  hit twice for the same data on every full run
- fetch_data.py's __main__ now fetches once, cleans, and saves the
  result to data/weather_2006_2026.csv - nothing downstream re-fetches
- load_data.py's __main__ now reads that CSV (with parse_dates=["date"])
  instead of calling the API - lets the DB be reloaded/reinitialized
  without burning API calls, useful after wiping the Docker volume
  
#### .gitignore

- Added data/*.csv - the generated CSV is regeneratable from the API
  and sizeable (7,500+ rows), no reason to track it in git
  
#### bug fixes caught while wiring this together

- Several syntax errors from manual edits (missing parens/quotes,
  swapped underscores, mismatched CSV_PATH casing) - caught one at a
  time by actually reading the tracebacks instead of guessing. Who knew
  tracebacks could be so helpful. In my defense it's 1am
- Missing `import time` in fetch_data.py (used by the sleep-between-
  requests rate limiting, previously untested until run end-to-end)
- CSV save initially failed with an OSError - was running the script
  from src/ instead of repo root, so the relative data/ path didn't
  resolve. Fixed by running from repo root: python src/run_pipeline.py
  
#### cross-machine Docker verification (Fedora)

- Docker on Fedora runs as a systemd service, not a background app -
  confirmed via systemctl status docker, no equivalent to Docker
  Desktop's menu bar indicator
- docker-compose (hyphenated) isn't installed on Fedora - Docker
  Desktop's standalone binary vs. the docker compose plugin (space)
  that ships via dnf install docker-compose-plugin
- MariaDB's container image ships its CLI as `mariadb`, not `mysql` -
  docker exec ... mysql fails with executable not found; mariadb is
  the correct binary name in newer MariaDB images
- Hit repeated access-denied errors that turned out to be several
  independent things stacking: mistyped passwords at hidden prompts,
  and this Fedora machine's .env using different DB_NAME
  (weather_db) and DB_ROOT_PASSWORD than assumed. Probally an issue with .env.example,
  given I used it to build the .env file on this new machine
- Set git user.name/user.email on Fedora machine (previously unset,
  commits were auto-attributing to a generic hostname-based identity)
  
#### verification

- Ran run_pipeline.py end-to-end from repo root on Fedora: 21 years
  fetched (2006-2026), cleaned, saved to CSV, loaded into daily_weather
- Confirmed via mycli: 7,525 rows, MIN(date)/MAX(date) = 2006-01-01 to
  2026-08-08, only 4 NULL rows (expected - NASA hasn't finalized the
  most recent few days yet)
- Committed on database-optimization branch, pushed, not yet merged
  to main - progress bar and log cleanup planned for tomorrow before
  merging

### Upcoming Plans
- Add tqdm instead of using the terminal logging. 
The terminal logging is unimaginably ugly and cluttered.
- Fix .env.example - its placeholder DB_NAME (weather_db) never
  actually matched the real convention used on my other machine.
   Copied the template as-is when setting up
  Fedora, which is exactly why the two .env files disagreed and
  caused repeated mycli/MariaDB access issues tonight.
  I've had similar problems in the past too,
  even locally on my Macbook. Which has the real .env on it!
 Wayyy too annoying to ignore at this point.
- Docker optimizations. Maybe.
- Oh and also Podman. Maybe. Since Fedora seems cool.
- UPDATING DOCUMENTATION. I know it's behind. Woefully so.
