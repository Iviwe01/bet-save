# app.py

import streamlit as st
import pandas as pd
from value_betting_core import fetch_odds, calibrate_probabilities, process_match_odds

st.set_page_config(page_title="Value Betting Dashboard", layout="wide")
st.title("⚽ Research-Only Value Betting Dashboard")

with st.sidebar:
    st.header("Settings")
    sport = st.selectbox("Sport", ["soccer_epl", "soccer_uefa_champs_league", "soccer_world_cup"])
    region = st.selectbox("Region", ["uk", "eu", "us", "au"])

# Example historical data
historical_df = pd.DataFrame({
    "result": ["home", "away", "home", "draw", "home", "away", "home"]
})
calibrated_probs = calibrate_probabilities(historical_df)

st.subheader("Live Odds & Suggested Bets")

try:
    odds_data = fetch_odds(sport=sport, region=region)
    rows = []
    for match in odds_data:
        rows.extend(process_match_odds(match, calibrated_probs))

    df = pd.DataFrame(rows)
    if df.empty:
        st.write("No data available. Check your API key or region/sport selection.")
    else:
        st.dataframe(df.sort_values("edge", ascending=False).reset_index(drop=True))

except Exception as e:
    st.error(f"Error fetching data:\n{e}")
