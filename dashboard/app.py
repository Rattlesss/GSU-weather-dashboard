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
tab1, tab2, tab3, tab4 = st.tabs([
    "Temperature & Precipitation",
    "Humidity & Wind",
    "Solar, Pressure & Correlations",
    "Closing thoughts"
])

with tab1:
# --- Temperature chart ---
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

# --- Precipitation chart ---
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
# --- Dual-chart split ---
    st.markdown("""
## Hot days here aren't necessarily dry days

You might expect temperature and humidity to move in opposite directions; 
hot days feeling muggy, cold days feeling crisp, but Bulloch County doesn't 
follow that pattern strongly. The two variables have a correlation of just 
-0.11 across 20 years of data, close to no relationship at all. Humidity 
sits anywhere from 50% to 90% at almost any temperature.

There's a slight tendency for the very hottest days to run a bit drier, 
visible as the scatter thins out toward the bottom right of the chart, 
but it's a weak effect, not a rule. What actually drives humidity down 
here is sunlight, not heat: solar radiation has a much stronger 
relationship with humidity (-0.58) than temperature does.

Wind tells a steadier story, for the most part. Daily wind speeds stay under 4 m/s on 
a typical day, with variations here and there. The single windiest day in the dataset fell on September 11, 
2017, with a speed of 8.78 m/s. Coincidentally, it's the same date as the county's second-largest precipitation 
event. Hurricane Irma didn't just bring rain here; it brought the 
strongest winds this dataset ever recorded.
""")

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

# --- explainer for the correlation figure cited in the narrative above ---
    st.markdown("""
**What "correlation" means here:** a number close to **+1** means two things 
tend to rise and fall together, like temperature and solar radiation. A 
number close to **-1** means one goes up as the other goes down, like 
humidity and solar radiation. A number near **0**, like the -0.11 between 
temperature and humidity above, means the two barely relate at all. 
Knowing one doesn't tell you much about the other.
""")

with tab3:
# --- Solar Radiation chart ---
    st.markdown("""
## Sunlight explains more about this climate than temperature does

Solar radiation follows the same clear seasonal rhythm as temperature, 
peaking in summer and dropping in winter, but it turns out to be the more 
useful number for explaining what else is happening on a given day. It has 
a stronger relationship with humidity (-0.58) than temperature does 
(-0.11): cloudier, more humid days block sunlight regardless of how hot or 
cold it is outside. Sunnier days also tend to run warmer too, with a +0.50 
correlation to temperature, but the humidity link is the stronger of the two.
""")

    st.subheader("Solar Radiation Over Time")
    fig_solar = px.line(filtered_df, x="date", y="solar_radiation_kwhm2",
                         labels={"date": "Date", "solar_radiation_kwhm2": "Solar Radiation (kWh/m²)"})
    fig_solar.update_traces(line_color="#FFD93D")
    fig_solar.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_solar, use_container_width=True)

# --- Surface Pressure chart ---
    st.markdown("""
## Pressure drops mark the storms

Surface pressure moves in a tighter, noisier band, mostly between 100 and 
102 kPa, with occasional sharp drops that mark the passage of low-pressure 
systems, including storms like the ones covered earlier in this dashboard. 
Pressure has a moderate negative relationship with temperature (-0.44): 
hotter days tend to come with slightly lower pressure, consistent with 
the unstable, storm-prone conditions that show up here in late summer 
and fall.
""")
    st.subheader("Surface Pressure Over Time")
    fig_pressure = px.line(filtered_df, x="date", y="surface_pressure_kpa",
                            labels={"date": "Date", "surface_pressure_kpa": "Surface Pressure (kPa)"})
    fig_pressure.update_traces(line_color="#6BCB77")
    fig_pressure.update_xaxes(minallowed=x_min, maxallowed=x_max)
    st.plotly_chart(fig_pressure, use_container_width=True)


# --- how to read the correlation grid ---
    st.markdown("""
## How to read the grid below

Every cell in this grid compares two variables and shows how closely they 
move together, on a scale from -1 to +1. It's the same idea introduced 
earlier with humidity and solar radiation, just applied to every 
combination of variables at once.

A value near **+1.00** means the two variables rise and fall together. 
Temperature and solar radiation, at +0.50, are a good example: sunnier 
days tend to be warmer days.

A value near **-1.00** means they move in opposite directions. Humidity 
and solar radiation, at -0.58, are the strongest example in this dataset: 
more sunlight tends to come with less humidity, and vice versa.

A value near **0.00** means the two barely relate at all. Temperature and 
humidity, at -0.11, fall into this category. Knowing the temperature on a 
given day tells you almost nothing about how humid it was.

The diagonal running from top-left to bottom-right is always **1.00**, 
because that's each variable compared to itself, a variable always 
correlates perfectly with its own values. It's not a meaningful result, 
just a byproduct of how the grid is built.

One important caveat: correlation isn't causation. A strong relationship 
between two variables doesn't prove one causes the other, only that they 
tend to move together. The humidity/solar link, for example, likely 
reflects a third factor, cloud cover, driving both at once, rather than 
either variable directly causing the other.
""")

    st.subheader("Correlation Between Variables")
    corr_columns = ["temperature_c", "precipitation_mm", "humidity_pct",
                     "wind_speed_ms", "solar_radiation_kwhm2", "surface_pressure_kpa"]
    corr = filtered_df[corr_columns].corr()
    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                          labels=dict(color="Correlation"))
    st.plotly_chart(fig_corr, use_container_width=True)

with tab4:
    st.markdown("""
## What the numbers agree on

Twenty years of daily data all point to the same conclusion: Bulloch 
County's weather isn't defined by any single variable. Solar radiation 
is the closest thing to a common thread, tying most strongly to both 
temperature and humidity, but even that relationship is moderate at best. 
Precipitation and wind barely correlate with anything else in the dataset, 
arriving on their own schedule regardless of what temperature, humidity, 
or pressure are doing that day.

That's the real takeaway from this dashboard. The averages are stable and 
predictable. The extremes, like a storm that drops 124mm in a day and is 
followed by a month of nothing, aren't. This is a county where the 
exceptions matter more than the rule.
""")

    st.subheader("Extremes and Baselines")

    variables = {
        "Temperature (°C)": "temperature_c",
        "Precipitation (mm)": "precipitation_mm",
        "Humidity (%)": "humidity_pct",
        "Wind Speed (m/s)": "wind_speed_ms",
        "Solar Radiation (kWh/m²)": "solar_radiation_kwhm2",
        "Surface Pressure (kPa)": "surface_pressure_kpa",
    }

    rows = []
    for label, col in variables.items():
        min_row = filtered_df.loc[filtered_df[col].idxmin()]
        avg_val = filtered_df[col].mean()
        max_row = filtered_df.loc[filtered_df[col].idxmax()]
        rows.append({
            "Variable": label,
            "Min": f"{min_row[col]:.2f} | {min_row['date'].strftime('%b %d, %Y')}",
            "Max": f"{max_row[col]:.2f} | {max_row['date'].strftime('%b %d, %Y')}",
            "Avg": f"{avg_val:.2f}",
        })

    extremes_df = pd.DataFrame(rows)
    # respects the sidebar date filter automatically, since it's built from filtered_df
    st.dataframe(extremes_df, use_container_width=True, hide_index=True)
    st.caption(
        "Min values of 0.00 for precipitation occur on many days across "
        "the dataset; the date shown is just the first occurrence, not a unique event."
    )
    
st.divider()

with st.expander("View raw data"):
    st.dataframe(filtered_df, use_container_width=True)

st.divider()
st.caption("Built by Rattles · NASA POWER API · Personal learning project, part of a GIS exploration series")

