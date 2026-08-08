import pandas as pd
from sqlalchemy import text
from db import engine

def load_weather_data(df: pd.DataFrame) -> None:
    """
       Loads a cleaned weather DataFrame into the daily_weather table.
       Uses "replace" logic so re-running the pipeline for the same
       dates doesn't create duplicates - batched via executemany
       instead of one execute() per row, since row-by-row crawls once
       we're loading years of data at once.

       Arguments:
           df: cleans DataFrame from clean_weather_data(), matching
               the daily_weather table columns.
       """
    # NASA POWER returns pd.NA for dates it hasn't published data for
    # yet (e.g. today). pymysql's executemany renders pd.NA as the
    # literal string "<NA>" instead of SQL NULL, so it must be
    # converted to None here before batching.
    def _clean(value):
        return None if pd.isna(value) else value

    rows = [
        {
            "date": row["date"].date(),
            "temperature_c": _clean(row["temperature_c"]),
            "precipitation_mm": _clean(row["precipitation_mm"]),
            "humidity_pct": _clean(row["humidity_pct"]),
            "wind_speed_ms": _clean(row["wind_speed_ms"]),
            "solar_radiation_kwhm2": _clean(row["solar_radiation_kwhm2"]),
            "surface_pressure_kpa": _clean(row["surface_pressure_kpa"]),
        }
        for _, row in df.iterrows()
    ]

    with engine.connect() as conn:
        # Passing a list of param dicts runs this as a single
        # executemany() batch instead of one round trip per row.
        conn.execute(
            text("""
            REPLACE INTO daily_weather
            (date, temperature_c, precipitation_mm, humidity_pct, wind_speed_ms,
            solar_radiation_kwhm2, surface_pressure_kpa)
            VALUES
            (:date, :temperature_c, :precipitation_mm, :humidity_pct, :wind_speed_ms,
            :solar_radiation_kwhm2, :surface_pressure_kpa)
            """),
            rows
        )
        conn.commit()


if __name__ == "__main__":
    import pandas as pd

    cleaned = pd.read.csv("data/weather_2006_2026.csv"), parse_dates=["date"])
    load_weather_data(cleaned)
    print(f"Loaded {len(cleaned)} rows into daily_weather)
