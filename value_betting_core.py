# value_betting_core.py

import requests
import pandas as pd
from config import ODDS_API_KEY, BANKROLL

def fetch_odds(sport="soccer_epl", region="uk", markets="h2h,totals"):
    """
    Fetch live odds from The Odds API.
    Returns the JSON response as Python objects.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": region,
        "markets": markets,
        "oddsFormat": "decimal"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def calibrate_probabilities(historical_df):
    """
    Create simple calibrated probabilities from historical results.
    Example: fraction of home/draw/away results.
    """
    counts = historical_df['result'].str.lower().value_counts(normalize=True)
    # Fallback probabilities if any outcome is missing
    return {
        "home": counts.get("home", 0.33),
        "draw": counts.get("draw", 0.33),
        "away": counts.get("away", 0.34)
    }

def implied_probability(odds):
    return 1.0 / odds if odds > 0 else 0.0

def edge(prob_model, odds):
    """Expected value edge = (model_prob * odds) - 1"""
    return (prob_model * odds) - 1

def kelly_fraction(prob, odds):
    """
    Fractional Kelly formula: f* = (bp - q)/b where b = odds - 1, q = 1 - p
    """
    b = odds - 1.0
    q = 1.0 - prob
    if b <= 0:
        return 0.0
    f = (b * prob - q) / b
    return max(f, 0.0)

def suggest_stake(prob, odds):
    """
    Suggested stake given model probability and odds.
    Uses Kelly fraction scaled by bankroll.
    """
    f = kelly_fraction(prob, odds)
    stake = f * BANKROLL
    return round(stake, 2)

def process_match_odds(match, calibrated_probs):
    """
    Given a match entry from Odds API plus calibrated_probs dict,
    generate rows for each market/outcome with edge and stake.
    """
    rows = []
    match_str = f"{match.get('home_team')} vs {match.get('away_team')}"
    for bookmaker in match.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            key = market.get("key")  # e.g. "h2h" or "totals"
            for outcome in market.get("outcomes", []):
                name = outcome.get("name").lower()
                odds = float(outcome.get("price"))
                # Determine which probability to use
                if key == "h2h":  # head-to-head: home/draw/away
                    prob_model = calibrated_probs.get(name, implied_probability(odds))
                else:
                    # For other markets (like totals), fallback to implied
                    prob_model = implied_probability(odds)
                imp_prob = implied_probability(odds)
                ev = edge(prob_model, odds)
                stake = suggest_stake(prob_model, odds)

                rows.append({
                    "match": match_str,
                    "market": key,
                    "outcome": name,
                    "odds": odds,
                    "prob_model": round(prob_model, 3),
                    "prob_implied": round(imp_prob, 3),
                    "edge": round(ev, 3),
                    "stake_suggested": stake,
                    "bookmaker": bookmaker.get("title")
                })
    return rows
