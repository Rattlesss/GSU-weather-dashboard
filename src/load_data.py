import pandas as pd
from sqlalchemy import text
from db import engine

def load_weather_data(df: pd.DataFrame) -> None:
    """
       Loads a cleaned weather DataFrame into the daily_weather table.
       Uses "replace" logic per row so re-running the pipeline for the
       same dates doesn't create duplicates.

       Arguments:
           df: cleans DataFrame from clean_weather_data(), matching
               the daily_weather table columns.
       """
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                REPLACE INTO daily_weather
                (date, temperature_c, precipitation_mm, humidity_pct, wind_speed_ms, 
                solar_radiation_kwhm2, surface_pressure_kpa)
                VALUES 
                (:date, :temperature_c, :precipitation_mm, :humidity_pct, :wind_speed_ms, 
                :solar_radiation_kwhm2, :surface_pressure_kpa)
                """),
                {
                    "date": row["date"].date(),
                    "temperature_c": row["temperature_c"],
                    "precipitation_mm": row["precipitation_mm"],
                    "humidity_pct": row["humidity_pct"],
                    "wind_speed_ms": row["wind_speed_ms"],
                    "solar_radiation_kwhm2": row["solar_radiation_kwhm2"],
                    "surface_pressure_kpa": row["surface_pressure_kpa"],
                }
            )
        conn.commit()


if __name__ == "__main__":
    from fetch_data import fetch_weather_data
    from clean_data import clean_weather_data

    raw = fetch_weather_data("20250101", "20251231")
    cleaned = clean_weather_data(raw)
    load_weather_data(cleaned)
    print(f"Loaded {len(cleaned)} rows into daily_weather")