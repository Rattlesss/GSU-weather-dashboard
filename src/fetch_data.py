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

if __name__ == "__main__":
    data = fetch_weather_data("20250101", "20251231")
    print(data["properties"]["parameter"].keys())