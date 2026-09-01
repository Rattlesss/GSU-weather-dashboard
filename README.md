# GSU Weather Dashboard

A live dashboard that pulls ~20 years of daily weather data for the Georgia Southern University area (Statesboro, Bulloch County, GA) from NASA's POWER API, stores it in MariaDB, and displays it with Streamlit.

This was my first solo Python/SQL project, done as a step towards future Data Engineering / ETL projects.

**Live dashboard:** [rattles.dev](https://rattles.dev/projects) links to the deployed version, hosted on Streamlit Community Cloud against a managed Aiven MariaDB instance. Nothing below is needed just to view it.

## What it does

Pulls ~20 years of daily weather data (temperature, precipitation, humidity, wind speed, solar radiation, surface pressure) from 2006–present, cleans it, loads it into a database, and shows it on an OWID-style dashboard (explanation-first, chart-supports-narrative) with a metric/imperial unit toggle, filters, and charts.

The live database is kept current automatically — a GitHub Actions workflow re-runs the pipeline on a weekly schedule (see [Keeping data current](#keeping-data-current) below).

## Tech stack

Python (requests, pandas, SQLAlchemy, PyMySQL, python-dotenv), MariaDB (Dockerized locally, Aiven in prod), Streamlit, Plotly, GitHub Actions

## Running it locally

Everything below spins up your own local copy — a local Dockerized MariaDB instance, populated by running the pipeline yourself. This is unrelated to the live rattles.dev deployment above.

1. Clone the repo:
```
git clone https://github.com/<your-username>/GSU-weather-dashboard.git
cd GSU-weather-dashboard
```

2. Copy the example env file and fill in real values:
```
cp .env.example .env
```

3. Run setup — creates the venv, installs dependencies, and brings up the MariaDB container (waits until it's healthy):
```
source setup.sh
```

4. Run the pipeline and launch the dashboard:
```
./run.sh
```

`schema.sql` is applied automatically when the MariaDB container first initializes (mounted via `docker-entrypoint-initdb.d` in `docker-compose.yml`), so there's no separate manual schema step.

## Keeping data current

`.github/workflows/update-data.yml` runs `src/run_pipeline.py` on a weekly cron schedule (Mondays, 6 AM UTC) using GitHub-hosted runners, so the live dashboard stays up to date without needing my own machine on. It can also be triggered manually from the Actions tab (`workflow_dispatch`) instead of waiting for the schedule.

The workflow needs six repo secrets for the database connection: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `DB_USE_SSL` (set to `true` — Aiven requires SSL, unlike the local Docker setup below). Streamlit Cloud's app secrets need the same six values for the dashboard itself to connect.

Note: the pipeline writes an intermediate CSV during the run, but GitHub Actions runners are ephemeral — that file does not persist anywhere after the job finishes. The database (Aiven) is the only durable copy of the data right now.

## Data source

NASA POWER API (power.larc.nasa.gov). Data is from the MERRA2 reanalysis model, not direct station observations.
 
## Note
 
I used Claude (AI) throughout this project to learn Python, SQL, and Streamlit as I went, since this was my first solo project in this stack. It walked me through things like setting up a virtual environment, writing the SQLAlchemy connection, and reshaping the NASA API's nested JSON into a flat table.
 
I made the actual decisions along the way, like expanding from the original 2 to 6 weather variables, starting with a native MariaDB install before later containerizing with Docker, and how to size and document the schema. I also caught and fixed a number of real bugs myself while testing each piece, including typos in column names, a missing SQL clause, and a wrong missing-value code. All of these decisions can be found in the DEVLOG.md along with all my notes.

I'm being upfront about this because I think it's a normal way to learn in our current coding environment, and I'd rather explain the process honestly than pretend I wrote all of this unaided. Tl;Dr Claude was used to aid the learning process, and was not used to replace human decision-making or structural decisions. It only served to help as a learning tool. All decisions are self-made.
 
## Author
 
Rattles
