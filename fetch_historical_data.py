# fetch_historical_data.py
# Scarica dati storici (fittizio) per un market e un intervallo di date, li salva in npy per l'hypertuning.

import argparse
import requests
import numpy as np
import logging
from config import HISTORY_LENGTH, FUTURE_STEPS

logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, help="Market address")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Endpoint fittizio: da sostituire con una vera API di dati storici
    url = f"https://api.example.com/historical?market={args.market}&start={args.start}&end={args.end}"
    # Eseguiamo una richiesta (fittizia, richiede un server reale)
    logger.info(f"Fetching historical data from {url}")
    response = requests.get(url)
    data = response.json()  # Aspettiamo lista di dict con: {"mid_price":..., "spread":..., "volume":...}

    data_buffer = []
    for d in data:
        data_buffer.append([d["mid_price"], d["spread"], d["volume"]])

    # Aggiunge features ma_10 e volatility_10 a tutti i punti
    for i in range(len(data_buffer)):
        if i < 10:
            ma_10 = data_buffer[i][0]
            vol_10 = 0.0
        else:
            prices = [data_buffer[j][0] for j in range(i-10, i)]
            ma_10 = np.mean(prices)
            returns = np.diff(np.log(prices))
            vol_10 = np.std(returns)
        data_buffer[i].append(ma_10)
        data_buffer[i].append(vol_10)

    # genera label (1 se prezzo futuro > prezzo attuale)
    mid_prices = [d[0] for d in data_buffer]
    y = []
    for i in range(HISTORY_LENGTH, len(data_buffer)-FUTURE_STEPS):
        future_price = mid_prices[i+FUTURE_STEPS]
        current_price = mid_prices[i]
        y.append(1 if future_price > current_price else 0)

    # genera X
    # X shape: (N, HISTORY_LENGTH, len(FEATURE_COLS))
    N = len(y)
    X = []
    for i in range(HISTORY_LENGTH, len(data_buffer)-FUTURE_STEPS):
        X.append(data_buffer[i-HISTORY_LENGTH:i])
    X = np.array(X)
    y = np.array(y)

    np.save("historical_data.npy", X)
    np.save("historical_labels.npy", y)
    logger.info("Dati storici salvati in historical_data.npy e historical_labels.npy")

if __name__ == "__main__":
    main()
