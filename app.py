# app.py
import streamlit as st
import pandas as pd
from value_betting_core import fetch_live_odds, estimate_probabilities, calculate_ev, suggest_bet
from config import BANKROLL

st.title("Smart Bet Saver Dashboard")

# --- Fetch live odds ---
st.sidebar.header("Fetch Live Odds")
if st.sidebar.button("Load Today's Matches"):
    try:
        live_df = fetch_live_odds()
        live_df['date'] = pd.to_datetime(live_df['date'])
        live_df = estimate_probabilities(live_df)
        live_df = live_df.apply(calculate_ev, axis=1)
        
        # Suggested bets
        bets, stakes = [], []
        for _, row in live_df.iterrows():
            bet, stake = suggest_bet(row, BANKROLL)
            bets.append(bet)
            stakes.append(round(stake, 2))
        live_df['Suggested Bet'] = bets
        live_df['Stake'] = stakes
        
        st.session_state['live_df'] = live_df
        st.success("Live odds loaded and bets calculated!")
    except Exception as e:
        st.error(str(e))

if 'live_df' in st.session_state:
    df = st.session_state['live_df']
    
    # --- Filters ---
    leagues = df['league'].unique()
    selected_league = st.sidebar.selectbox("Select League", leagues)
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    
    filtered_df = df[(df['league'] == selected_league) & (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
    
    if len(filtered_df) == 0:
        st.warning("No matches found for selected filters.")
    else:
        # Highlight highest EV
        def highlight_max(s):
            is_max = s == s.max()
            return ['background-color: lightgreen' if v else '' for v in is_max]
        
        ev_columns = ['ev_home','ev_draw','ev_away']
        st.subheader("Predictions & Suggested Bets")
        st.dataframe(filtered_df.style.apply(highlight_max, subset=ev_columns))

