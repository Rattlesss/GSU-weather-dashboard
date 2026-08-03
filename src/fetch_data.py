import time

import requests

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
    response.raise_for_status() # raises an error if the
    return response.json()


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
    for year in range(start_year, end_year + 1):
        # Only clip the start/end chunk to the requested start_date/
        # end_date; every year in between runs Jan 1 - Dec 31.
        chunk_start = start_date if year == start_year else f"{year}0101"
        chunk_end = end_date if year == end_year else f"{year}1231"

        chunk = fetch_weather_data(chunk_start, chunk_end)

        if merged is None:
            merged = chunk
        else:
            for param, values in chunk["properties"]["parameter"].items():
                merged["properties"]["parameter"][param].update(values)

        if year != end_year:
            time.sleep(sleep_seconds)

    return merged


if __name__ == "__main__":
    from datetime import date

    today = date.today().strftime("%Y%m%d")
    data = fetch_weather_data_range("20060101", today)
    print(data["properties"]["parameter"].keys())