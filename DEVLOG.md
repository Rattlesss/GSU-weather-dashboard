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



## August 9, 2026

#### Dev notes

- Today was pretty slow. Hit a venv error like an idiot. 
  Installed packages to Fedora using dnfbefore realizing what I was doing.
  I use Brew / Linuxbrew for all dev stuff, and want to keep them seperate.
  Wasn't too bad of a mistake though, I just needed pip for something.
- Note to self: when you swap machines, ensure you're in the venv
- Will probally be getting more active with this project. Have some fun things planned.

#### fetch_data.py - progress bar & colored output
- Replaced the per-year logger.info() calls with a live tqdm progress
  bar (desc="Fetching NASA POWER data", unit="year") - routine
  "fetching year X / received Y days / sleeping" chatter is now just
  the bar advancing, instead of 60+ scrolling log lines per run.
- Added a postfix on the bar (pbar.set_postfix(year=year,
  days=total_days)) - shows the current year and running row count
  live, rather than only knowing progress by percentage.
- Kept one thing worth still calling out explicitly: any year
  returning fewer than 360 days gets a tqdm.write() note, since the
  bar alone wouldn't surface that.
- Colored that note with raw ANSI codes (yellow for "Note:", cyan for
  the day count) rather than pulling in a new dependency - considered
  rich for this, decided it's overkill for one colored line.
- Caught a handful of small bugs while wiring this in: a typo in the
  RESET escape code (\093 instead of \033), color constants
  accidentally scoped inside the loop instead of once above the
  function, and total_days never actually being incremented in an
  earlier draft.
- Added a short comment on the `if __name__ == "__main__":` guard.
  It's not obvious at a glance why it's there, added to reduce confusion.

#### verification
- Ran run_pipeline.py twice back to back - colored output rendered
  correctly in terminal, bar/postfix updated live, both runs loaded
  7,525 rows in ~34-35s with identical results.

#### theorizing, not yet implemented: incremental fetching
- Current pipeline always re-fetches the full 2006-2026 range on every
  run, even though only the last ~90 days (NASA's not-yet-finalized
  window) plus any new days actually change.
- Main Idea: check MAX(date) already in daily_weather (or
  in the CSV), then only fetch from ~90 days before that through
  'today' - existing REPLACE INTO logic already handles the overlap
  safely.
- Doesn't require anything running constantly - this only matters for
  runs after the initial backfill, and stays a manually-triggered
  script until/unless a scheduler gets added later.
- Not implemented yet - next optimization in line. Maybe. Needs more research.

### Still open
- Incremental fetching (see above)
- Dashboard redesign - not started
- .env.example / DB_NAME convention still inconsistent between machines
- Error handling/retries on the fetch loop
- database-optimization branch verified working, not yet merged to main
- Potential webpage integration using GCP. Part of broader idea. Far on timeline.



## August 13, 2026

#### setup.sh, run.sh

- Added two cross-platform scripts to stop re-doing setup steps
  every time I switch machines: setup.sh (creates venv if missing,
  installs requirements, copies .env.example if .env is missing,
  auto-detects docker compose vs docker-compose, brings up the
  container and waits for healthy) and run.sh (runs the pipeline,
  then launches the dashboard)
- Auto-detection matters because Fedora only has the docker compose
  plugin (space), not the standalone docker-compose binary MacOS has.
  Same underlying issue from a few nights ago, now handled
  automatically. I'll forget otherwise.
- First real run on the Mac created a completely fresh venv (the old
  one apparently wasn't there anymore) and caught that tqdm wasn't
  installed there yet. This is exactly the kind of gap this script exists to
  catch
- Committed these on the wrong branch (database-optimization
  instead of feature/dashboard-redesign) before realizing. Refered
  to claude and pulled the two commits over cleanly via a merge into 
  main. I'm getting a lot better with Git CLI, but mistakes like this
  scare me. I really want to maintain a clean dev tree.

#### the .env issues, hopefully actually resolved this time

- Root cause behind weeks of intermittent access-denied errors: three
  separate issues all at once (mistyped passwords at hidden prompts,
  MariaDB only applying .env values on first container init, and
  different .Env values across machines)
- Decided the actual fix isn't a better .env.example, it's just
  writing the real values down somewhere durable. Set up Bitwarden,
  saved the finalized credentials there
- Reconciled both machines' real .env files to match going forward
- Fedora and MacOS now both have updated .Env files. Problem appears
  to be fixed. Will revisit at first instance of failure. I'm tired
  of dealing with this exact same problem. I just want my DB to work.



## August 16, 2026

#### dashboard redesign, feature/dashboard-redesign branch

- Rebuilt all three original tabs (Temperature & Precipitation,
  Humidity & Wind, Solar/Pressure/Correlations) with real narrative
  sections instead of bare charts.Added claim-first headers, context
  paragraphs before each chart, "OWID-style" but with more text than
  OWID typically uses
- Queried the actual data instead of guessing at "interesting"
  moments: confirmed the all-time wettest day (Oct 7, 2016, 124.51mm)
  and the longest dry streak (Oct 16-Nov 12, 2016, 28 days) both trace
  back to Hurricane Matthew, and the single windiest day (Sept 11,
  2017, 8.78 m/s) is the same date as the second-largest rainfall
  event; Hurricane Irma
- Fixed a real bug in a DATEDIFF-based streak query along the way:
  wrong syntax was silently producing 3,938 warnings and one bogus
  3,938-day "streak". Still have some learning to do with SQL.
- Added a "how to read this" explainer for the correlation heatmap,
  written for someone with zero stats background, plus a causation
  caveat
- Added a 4th tab: min/max/avg table for all six
  variables, dates folded into each cell, plus the correlation
  conclusion moved here as a standalone closer
- Fixed the metric cards showing dates with no year (leftover from
  the single-year version) and hid the misleading up/down delta
  arrows via a small CSS override, since Streamlit has no built-in
  way to suppress just the icon
- Merged into main via --no-ff, going forward that's my standard for
  every branch merge from here on, want the diverge/reconverge shape
  visible in the git graph



## August 16, 2026

#### rattles.dev

- Built my personal portfolio site, hosted on GitHub Pages, Astro +
  plain HTML/CSS
- Added a project card for the weather dashboard: casual-but-technical
  blurb, correctly called it an ETL pipeline, tags for the actual
  stack (Python, ETL Pipeline, NASA API, MariaDB, Docker, Streamlit,
  Plotly)

#### went public: Aiven + Streamlit Community Cloud

- Deployed for real: MariaDB moved to Aiven (managed hosting),
  dashboard deployed on Streamlit Community Cloud, both linked from
  rattles.dev
- Learned that Aiven's free tier auto-powers-off unused
  services: confirmed via the event log; not a bug, just the
  documented behavior
- Upgraded to Aiven's Developer tier to stop the auto-shutoffs going
  forward, using existing trial credit rather than paying immediately



## August 19, 2026

#### scheduled data refresh via GitHub Actions

- Realized the deployed version has no way to stay current on its
  own - Streamlit Cloud only reads from Aiven, it never runs the
  pipeline. Someone (me) has to actually trigger a refresh
- Added .github/workflows/update-data.yml: runs run_pipeline.py on a
  weekly cron schedule, using GitHub-hosted runners and repo secrets
  for the Aiven credentials - zero dependency on my own machine being
  on
- Also added workflow_dispatch so it can be triggered manually from
  the Actions tab without waiting for the schedule
- Weekly instead of daily for now, full 20-year re-fetch every day
  felt wasteful. The incremental-fetch idea from a few nights ago is
  still on the table if this needs to run more often later
- Clarified for myself how prod actually works now: dashboard-only
  code changes just need a git push to main and Streamlit Cloud
  picks it up automatically. Anything that changes what's actually in
  the database needs to be run against Aiven directly, not just
  pushed as code

### Running ideas
- Incremental fetching (still theorized, not built - matters more now
  that there's an actual recurring scheduled job)
- Error handling/retries on the fetch loop
- Streamlit not containerized (Docker still only wraps MariaDB
  locally)
- HP Pavilion server - now its own separate project/thread, not
  starting until rattles.dev and the dashboard redesign were solidly
  done (they are now)
- Dashboard additons: Metric/SAE slider, more narative work, coloring
