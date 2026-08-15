from sqlalchemy import text
from db import engine

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_weather (
    date DATE NOT NULL PRIMARY KEY COMMENT 'Calendar date (YYYY,MM,DD)',
    temperature_c DECIMAL(5,2) COMMENT 'T2M - Temperature at 2 meter, Celsius',
    precipitation_mm DECIMAL(6,2) COMMENT 'PRECTOTCORR - Precipitation corrected, mm/day',
    humidity_pct DECIMAL(5,2) COMMENT 'RH2M - Relative humidity at 2 meters, percent',
    wind_speed_ms DECIMAL(5,2) COMMENT 'WS2M - Wind speed at 2 meters, meters/second',
    solar_radiation_kwhm2 DECIMAL(6,2) COMMENT 'ALLSKY_SFC_SW_DWN - Solar radiation, KWh/m2/day',
    surface_pressure_kpa DECIMAL(6,2) COMMENT 'PS - Surface pressure, kPa'
)
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text(SCHEMA))
        conn.commit()
        print("Table created (or already existed).")
