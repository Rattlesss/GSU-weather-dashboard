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
#### Day 1 (continued) — schema design
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