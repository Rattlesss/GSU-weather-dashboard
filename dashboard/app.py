import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from db import engine

st.set_page_config(page_title="GSU Weather Dashboard", page_icon="🌦️", layout="wide")


@st.cache_data
def load_data():
    query = "SELECT * FROM daily_weather ORDER BY date"
    df = pd.read_sql(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


try:
    df = load_data()
except Exception as e:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()

# ---- Header ----
st.title("GSU / Bulloch County Weather Dashboard")
st.caption("Data source: NASA POWER API (MERRA2 reanalysis model) · "
           "Location: 32.4194°N, -81.7767°W")
st.markdown(
    "This dashboard explores 20 years of daily weather data for the "
    "Georgia Southern University area, pulled from NASA's POWER API. "
    "Built as a first project in a personal learning series toward a GIS-based exploration."
)

# ---- Sidebar filters ----
st.sidebar.header("Filters")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Edge case: user hasn't finished picking a full range yet
if len(date_range) != 2:
    st.warning("Please select both a start and end date in the sidebar.")
    st.stop()

start_date, end_date = date_range
mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
filtered_df = df.loc[mask]

if filtered_df.empty:
    st.error("No data available for the selected date range.")
    st.stop()

st.sidebar.caption(f"Showing {len(filtered_df)} of {len(df)} days")

# x-axis bounds for all time-series charts, so panning/zooming can't
# drift past the actual data range
x_min = filtered_df["date"].min()
x_max = filtered_df["date"].max()

# ---- Summary metrics ----
st.markdown("""
<style>
[data-testid="stMetricDelta"] svg {
    display: none;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

hottest_day = filtered_df.loc[filtered_df["temperature_c"].idxmax()]
coldest_day = filtered_df.loc[filtered_df["temperature_c"].idxmin()]
wettest_day = filtered_df.loc[filtered_df["precipitation_mm"].idxmax()]
avg_humidity = filtered_df["humidity_pct"].mean()

col1.metric("Hottest Day", f"{hottest_day['temperature_c']:.1f} °C",
            hottest_day["date"].strftime("%b %d, %Y"))
col2.metric("Coldest Day", f"{coldest_day['temperature_c']:.1f} °C",
            coldest_day["date"].strftime("%b %d, %Y"))
col3.metric("Wettest Day", f"{wettest_day['precipitation_mm']:.1f} mm",
            wettest_day["date"].strftime("%b %d, %Y"))
col4.metric("Avg Humidity", f"{avg_humidity:.1f}%")

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs([
    "Temperature & Precipitation",
    "Humidity & Wind",
    "Solar, Pressure & Correlations"
])

with tab1:
# --- narrative section, added before the temperature chart ---
    st.markdown("""
## The swing matters more than the average

Bulloch County doesn't have a single "typical" day. Over the past 20 years, 
temperatures here have ranged from a low of -5.1°C to a high of 33.3°C, 
nearly a 40 degree difference between the coldest and hottest days on 
record. Summers climb into the low 30s with predictable regularity, while 
winters dip well below freezing more often than the region's reputation 
might suggest.

That rhythm shows up clearly in the chart below: sharp, repeating peaks 
every summer, deep valleys every winter, with almost no flat stretches 
in between. This isn't a place with a mild in-between season. It swings 
hard, twice a year, every year.
""")

    st.subheader("Temperature Over Time")
    fig_temp = px.line(filtered_df, x="date", y="temperature_c",
                        labels={"date": "Date", "temperature_c": "Temperature (°C)"})
    fig_temp.update_traces(line_color="#FF6B6B")
    fig_temp.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_temp, use_container_width=True)

# --- narrative section, added before the precipitation chart ---
    st.markdown("""
## Statesboro's wettest day was followed by its driest month

On October 7, 2016, Bulloch County recorded 124.51mm of rain in a single day, 
the most rainfall this dataset has ever seen here. It wasn't an ordinary 
storm: Hurricane Matthew's winds tore through the area overnight, killing 
two people in Statesboro when trees fell on their homes early the next 
morning, and leaving thousands without power for days.

What's stranger is what happened next. Rather than a wet aftermath, the 
region swung hard the other way. From October 16 to November 12, 2016, 
Bulloch County went 28 consecutive days with essentially no rain, the 
longest dry stretch in the past 20 years. The same month that brought the 
area's worst flooding also produced its driest spell.

It's a pattern that shows up elsewhere in the data too. A little under a 
year later, Hurricane Irma brought another sharp spike, 74.94mm on 
September 11, 2017, but nothing close to the drought that followed 
Matthew. Big rain events here tend to be isolated, sudden, and gone almost 
as fast as they arrived.
""")

    st.subheader("Precipitation Over Time")
    fig_precip = px.bar(filtered_df, x="date", y="precipitation_mm",
                         labels={"date": "Date", "precipitation_mm": "Precipitation (mm)"})
    fig_precip.update_traces(marker_color="#4D96FF")
    fig_precip.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_precip, use_container_width=True)

with tab2:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Humidity vs Temperature")
        fig_scatter = px.scatter(filtered_df, x="temperature_c", y="humidity_pct",
                                  labels={"temperature_c": "Temperature (°C)",
                                          "humidity_pct": "Humidity (%)"},
                                  opacity=0.6)
        fig_scatter.update_traces(marker_color="#95D5B2")
        # no x-axis constraint here - this isn't a date-based chart
        st.plotly_chart(fig_scatter, use_container_width=True)

    with chart_col2:
        st.subheader("Wind Speed Over Time")
        fig_wind = px.line(filtered_df, x="date", y="wind_speed_ms",
                            labels={"date": "Date", "wind_speed_ms": "Wind Speed (m/s)"})
        fig_wind.update_traces(line_color="#B39CD0")
        fig_wind.update_xaxes(minallowed=x_min, maxallowed=x_max)
        st.plotly_chart(fig_wind, use_container_width=True)

with tab3:
    st.subheader("Solar Radiation Over Time")
    fig_solar = px.line(filtered_df, x="date", y="solar_radiation_kwhm2",
                         labels={"date": "Date", "solar_radiation_kwhm2": "Solar Radiation (kWh/m²)"})
    fig_solar.update_traces(line_color="#FFD93D")
    fig_solar.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_solar, use_container_width=True)

    st.subheader("Surface Pressure Over Time")
    fig_pressure = px.line(filtered_df, x="date", y="surface_pressure_kpa",
                            labels={"date": "Date", "surface_pressure_kpa": "Surface Pressure (kPa)"})
    fig_pressure.update_traces(line_color="#6BCB77")
    fig_pressure.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_pressure, use_container_width=True)

    st.subheader("Correlation Between Variables")
    corr_columns = ["temperature_c", "precipitation_mm", "humidity_pct",
                     "wind_speed_ms", "solar_radiation_kwhm2", "surface_pressure_kpa"]
    corr = filtered_df[corr_columns].corr()
    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                          labels=dict(color="Correlation"))
    # no x-axis constraint here either - it's a heatmap, not a time series
    st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

with st.expander("View raw data"):
    st.dataframe(filtered_df, use_container_width=True)

st.divider()
st.caption("Built by Rattles · NASA POWER API · Personal learning project, part of a GIS exploration series")
