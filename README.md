# GSU Weather Dashboard
 
A dashboard that pulls daily weather data for the Georgia Southern University area (Statesboro, Bulloch County, GA) from NASA's POWER API, stores it in MariaDB, and displays it with Streamlit.
 
This was my first solo Python/SQL project, done as a step toward a future GIS-based capstone project.
 
## What it does
 
Pulls a year of daily weather data (temperature, precipitation, humidity, wind speed, solar radiation, surface pressure), cleans it, loads it into a database, and shows it on a dashboard with filters and charts.
 
## Tech stack
 
Python (requests, pandas, SQLAlchemy, PyMySQL, python-dotenv), MariaDB, Streamlit, Plotly
 
## Setup
 
1. Clone the repo and set up a virtual environment:
```
git clone https://github.com/<your-username>/GSU-weather-dashboard.git
cd GSU-weather-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
 
2. Install MariaDB (Google if unsure how) and create the database:
```sql
CREATE DATABASE weather_project;
```
 
3. Create a `.env` file in the project root:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=weather_project
```
 
4. Create the table:
```
mysql -u root -p weather_project < src/schema.sql
```
 
5. Run the pipeline to fetch, clean, and load the data:
```
python src/load_data.py
```
 
6. Run the dashboard:
```
streamlit run dashboard/app.py
```
 
## Data source
 
NASA POWER API (power.larc.nasa.gov). Data is from the MERRA2 reanalysis model, not direct station observations.
 
## Note
 
I used Claude (AI) throughout this project to learn Python, SQL, and Streamlit as I went, since this was my first solo project in this stack. It walked me through things like setting up a virtual environment, writing the SQLAlchemy connection, and reshaping the NASA API's nested JSON into a flat table.
 
I made the actual decisions along the way, like expanding from the original 2 to 6 weather variables, choosing a native MariaDB install over Docker (I didn't want to overcomplicate things), and how to size and document the schema. I also caught and fixed a number of real bugs myself while testing each piece, including typos in column names, a missing SQL clause, and a wrong missing-value code.

I'm being upfront about this because I think it's a normal way to learn in our current coding environment, and I'd rather explain the process honestly than pretend I wrote all of this unaided.
 
## Author
 
Rattles
