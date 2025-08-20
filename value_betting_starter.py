# value_betting_starter.py

import pandas as pd
from value_betting_core import fetch_odds, calibrate_probabilities, process_match_odds

def run_cli():
    # Example historical data for calibration
    historical_df = pd.DataFrame({
        "result": ["home", "away", "home", "draw", "home", "away", "home"]
    })
    calibrated_probs = calibrate_probabilities(historical_df)

    print("Fetching live odds...")
    odds_data = fetch_odds()
    rows = []
    for match in odds_data:
        rows.extend(process_match_odds(match, calibrated_probs))

    df = pd.DataFrame(rows)
    if df.empty:
        print("No matches returned or data unavailable.")
        return

    # Sort by descending edge
    top = df.sort_values("edge", ascending=False).head(10)
    print(top.to_string(index=False))

if __name__ == "__main__":
    run_cli()
