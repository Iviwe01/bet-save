# value_betting_core.py
import pandas as pd
import numpy as np
import requests
from config import ODDS_API_KEY, SPORT, REGION, ODDS_FORMAT, BANKROLL

# --- Fetch live odds from The Odds API ---
def fetch_live_odds(sport=SPORT, region=REGION, odds_format=ODDS_FORMAT, api_key=ODDS_API_KEY):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "regions": region,
        "oddsFormat": odds_format,
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch odds: {response.status_code}")
    data = response.json()
    matches = []
    for game in data:
        for bookmaker in game['bookmakers']:
            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    outcomes = {o['name']: o['price'] for o in market['outcomes']}
                    matches.append({
                        'league': game['sport_title'],
                        'date': game['commence_time'],
                        'home_team': game['home_team'],
                        'away_team': game['away_team'],
                        'home_odds': outcomes.get(game['home_team'], np.nan),
                        'draw_odds': outcomes.get('Draw', np.nan),
                        'away_odds': outcomes.get(game['away_team'], np.nan)
                    })
    return pd.DataFrame(matches)

# --- Estimate probabilities directly from odds ---
def estimate_probabilities(df):
    df['prob_home'] = 1 / df['home_odds']
    df['prob_draw'] = 1 / df['draw_odds']
    df['prob_away'] = 1 / df['away_odds']
    
    # Normalize probabilities
    total = df['prob_home'] + df['prob_draw'] + df['prob_away']
    df['prob_home'] /= total
    df['prob_draw'] /= total
    df['prob_away'] /= total
    return df

# --- EV calculation ---
def calculate_ev(row):
    row['ev_home'] = row['prob_home'] * row['home_odds'] - 1
    row['ev_draw'] = row['prob_draw'] * row['draw_odds'] - 1
    row['ev_away'] = row['prob_away'] * row['away_odds'] - 1
    return row

# --- Suggest bet and stake ---
def suggest_bet(row, bankroll=BANKROLL):
    bets = {
        'Home': row['ev_home'],
        'Draw': row['ev_draw'],
        'Away': row['ev_away']
    }
    best_bet = max(bets, key=bets.get)
    if bets[best_bet] <= 0:
        return 'Skip', 0
    odds = row[f'{best_bet.lower()}_odds']
    prob = row[f'prob_{best_bet.lower()}']
    stake = bankroll * ((odds * prob - 1) / (odds - 1))  # Kelly criterion
    stake = max(0, stake)
    return best_bet, stake


