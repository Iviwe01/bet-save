# value_betting_core.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import requests
from config import ODDS_API_KEY, SPORT, REGION, ODDS_FORMAT, BANKROLL

# --- Train predictive model ---
def train_model(data_path="historical_data.csv"):
    df = pd.read_csv(data_path)
    le_home = LabelEncoder()
    le_away = LabelEncoder()
    df['home_encoded'] = le_home.fit_transform(df['home_team'])
    df['away_encoded'] = le_away.fit_transform(df['away_team'])
    
    X = df[['home_encoded', 'away_encoded', 'home_odds', 'draw_odds', 'away_odds']]
    y = df['result']  # 'H', 'D', 'A'
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    return model, le_home, le_away

# --- Predict probabilities for matches ---
def predict_match(model, le_home, le_away, df_matches):
    df_matches['home_encoded'] = le_home.transform(df_matches['home_team'])
    df_matches['away_encoded'] = le_away.transform(df_matches['away_team'])
    X = df_matches[['home_encoded', 'away_encoded', 'home_odds', 'draw_odds', 'away_odds']]
    probs = model.predict_proba(X)
    
    classes = model.classes_
    df_matches['prob_home'] = probs[:, list(classes).index('H')]
    df_matches['prob_draw'] = probs[:, list(classes).index('D')]
    df_matches['prob_away'] = probs[:, list(classes).index('A')]
    return df_matches

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

