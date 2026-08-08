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
