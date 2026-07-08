## Day 1 — July 8, 2026

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

