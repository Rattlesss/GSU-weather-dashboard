"""
Runs the full weather datat pipeline: fetch -> clean -> save CSV -> load into DB.
"""
from datetime import date
from fetch_data import fetch_weather_data_range
from clean_data import clean_weather_data
from load_data import load_weather_data

CSV_PATH = "../data/weather_2006_2026.csv"

def run_pipeline():
    today = date.today().strftime("%Y%m%d")

    print("Fetching data from NASA POWER API...")
    raw = fetch_weather_data_range("20060101", today)

    print("Cleaning data...")
    cleaned = clean_weather_data(raw)

    print(f"Saving to {CSV_PATH}...")
    cleaned.to_csv(CSV_PATH, index=False)

    print("Loading into database...")
    load_weather_data(cleaned)

    print(f"Done. Loaded {len(cleaned)} rows into daily_weather.")

if __name__ == "__main__":
    run_pipeline()
