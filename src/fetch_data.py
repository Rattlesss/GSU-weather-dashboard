import time
import logging
import requests
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

LATITUDE = 32.4194
LONGITUDE = -81.7767
PARAMETERS = "T2M,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PS"

def fetch_weather_data(start_date: str, end_date: str) -> dict:
    """
    Fetch daily weather data from the NASA POWER API for GSU / Bulloch County
    Arguments:
        start_date: YYYYMMDD string, e.g. "20250101"
        end_date: YYYYMMDD string, e.g. "20251231"
    Returns:
        Parsed JSON response as dict
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": PARAMETERS,
        "community": "RE",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Adds terminal colors during write (ANSI used for compatibility)
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def fetch_weather_data_range(start_date: str, end_date: str, sleep_seconds: float = 1.0) -> dict:
    """
    Fetch daily weather data across a long date range by looping
    year-by-year, rather than one massive request, to avoid NASA
    POWER's rate limiting/throttling.
    Arguments:
        start_date: YYYYMMDD string, e.g. "20060101"
        end_date: YYYYMMDD string, e.g. "20261231"
        sleep_seconds: pause between yearly requests, to be polite
            to the API.
    Returns:
        Parsed JSON dict shaped like a single fetch_weather_data()
        response, with every year's parameter values merged together.
    """
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    merged = None
    years = range(start_year, end_year + 1)
    pbar = tqdm(years, desc="Fetching NASA POWER data", unit='year')
    total_days = 0   # running count shown in progress bar

    for year in pbar:
        chunk_start = start_date if year == start_year else f"{year}0101"
        chunk_end = end_date if year == end_year else f"{year}1231"

        chunk = fetch_weather_data(chunk_start, chunk_end)
        num_days = len(next(iter(chunk["properties"]["parameter"].values())))
        total_days += num_days
        pbar.set_postfix(year=year, days=total_days)
    
        if num_days < 360:
            # NASA sometimes only returns partial years (Current year, missing data, etc)
            # Flags gaps without stopping the whole fetch
            tqdm.write(f"{YELLOW}Note:{RESET} {year} only returned {CYAN}{num_days}{RESET} days (Expected ~365){RESET}")

        if merged is None:
            merged = chunk
        else:
            for param, values in chunk["properties"]["parameter"].items():
                merged["properties"]["parameter"][param].update(values)

        if year != end_year:
            time.sleep(sleep_seconds)

    return merged

if __name__ == "__main__":
    # Runs when the file is executed directly ("python src/fetch_data.py")
    # Skipped when functions imported elsewhere ("python run_pipeline.py")
    from datetime import date
    from clean_data import clean_weather_data
    today = date.today().strftime("%Y%m%d")
    raw = fetch_weather_data_range("20060101", today)
    cleaned = clean_weather_data(raw)
    cleaned.to_csv("data/weather_2006_2026.csv", index=False)
    print(f"Saved {len(cleaned)} rows to data/weather_2006_2026.csv")
