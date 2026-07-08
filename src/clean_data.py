import pandas as pd


def clean_weather_data(raw_json: dict) -> pd.DataFrame:
    """
    Transform NASA POWER API JSON response into a clean DataFrame,
    one row per date, matching the daily_weather table schema.

    Arguments:
        raw_json the dict returned by fetch_weather_data()

    Returns:
        pandas DataFrame with columns matching daily_weather table.
    """
    parameters = raw_json["properties"]["parameter"]

    # Each parameter is a dict of {date_string: value}.
    # Builds one DataFrame per parameter, then joins them all on date.
    df = pd.DataFrame(parameters)

    # Fetched dates index as "20250101"
    # Converts to real datetime, then to a clean date column.
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"
    df = df.reset_index()

    # Renames API parameter names to match schema.sql column names.
    df = df.rename(columns={
        "T2M": "temperature_c",
        "PRECTOTCORR": "precipitation_mm",
        "RH2M": "humidity_pct",
        "WS2M": "wind_speed_ms",
        "ALLSKY_SFC_SW_DWN": "solar_radiation_kwhm2",
        "PS": "surface_pressure_kpa"
    })

    # NASA POWER uses -999 as a missing value code; replaces with
    # actual N/A so it doesn't get treated as a real reading.

    df = df.replace(-999, pd.NA)

    return df


if __name__ == "__main__":
    from fetch_data import fetch_weather_data

    raw = fetch_weather_data("20250101", "20251231")
    cleaned = clean_weather_data(raw)
    print(cleaned.head())
    print(cleaned.shape)
