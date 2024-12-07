# tune_model.py
# Hypertuning con keras-tuner sui dati storici generati dal bot (live_data.csv)

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
import keras_tuner as kt
from config import HISTORY_LENGTH, FUTURE_STEPS, FEATURE_COLS, PRETRAINED_MODEL_PATH
import logging

logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def build_model(hp):
    model = Sequential()
    model.add(LSTM(units=hp.Int('units1', 64, 256, step=64), return_sequences=True, input_shape=(HISTORY_LENGTH, len(FEATURE_COLS))))
    model.add(LSTM(units=hp.Int('units2', 32, 128, step=32)))
    model.add(Dense(1, activation='sigmoid'))
    lr = hp.Float('lr', 1e-4, 1e-2, sampling='log')
    model.compile(optimizer=Adam(lr), loss='binary_crossentropy', metrics=['accuracy'])
    return model

def add_features_to_data(data):
    # data: array/list di [mid_price, spread, volume] per ogni riga
    # Aggiungiamo ma_10, volatilità_10
    full_data = []
    for i in range(len(data)):
        if i < 10:
            ma_10 = data[i][0]
            vol_10 = 0.0
        else:
            prices_window = [data[j][0] for j in range(i-10, i)]
            ma_10 = np.mean(prices_window)
            returns = np.diff(np.log(prices_window))
            vol_10 = np.std(returns)
        full_data.append(data[i] + [ma_10, vol_10])
    return full_data

def main():
    # Carica i dati da live_data.csv
    df = pd.read_csv("live_data.csv")  # Contiene timestamp, mid_price, best_bid, best_ask, spread, volume

    # Estraiamo le colonne necessarie per il modello di base: mid_price, spread, volume
    raw_data = df[["mid_price", "spread", "volume"]].values

    # Aggiunge le feature avanzate
    full_data = add_features_to_data(raw_data)
    # full_data è una lista di [mid_price, spread, volume, ma_10, volatility_10]

    full_data = np.array(full_data)

    # Generiamo le label
    # Label: 1 se prezzo FUTURE_STEPS avanti > prezzo attuale, altrimenti 0
    mid_prices = full_data[:, 0]  # mid_price è la prima colonna
    y = []
    for i in range(HISTORY_LENGTH, len(full_data)-FUTURE_STEPS):
        future_price = mid_prices[i+FUTURE_STEPS]
        current_price = mid_prices[i]
        y.append(1 if future_price > current_price else 0)
    y = np.array(y)

    # Genera X
    # X shape: (N, HISTORY_LENGTH, len(FEATURE_COLS))
    # FEATURE_COLS = ["mid_price", "spread", "volume", "ma_10", "volatility_10"]
    N = len(y)
    X = []
    for i in range(HISTORY_LENGTH, len(full_data)-FUTURE_STEPS):
        X.append(full_data[i-HISTORY_LENGTH:i])
    X = np.array(X)

    # Dividiamo in train/validation
    N = len(y)
    split = int(N*0.8)
    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    tuner = kt.RandomSearch(
        build_model,
        objective='val_accuracy',
        max_trials=5,
        executions_per_trial=1,
        directory='tuner_results',
        project_name='solana_trader'
    )

    logger.info("Inizio hypertuning...")
    tuner.search(X_train, y_train, epochs=5, validation_data=(X_val, y_val))
    best_model = tuner.get_best_models(num_models=1)[0]
    best_model.save(PRETRAINED_MODEL_PATH)
    logger.info("Hypertuning completato, miglior modello salvato in model.h5")

if __name__ == "__main__":
    main()
