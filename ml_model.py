# ml_model.py
# Gestione del modello ML: creazione, caricamento, training incrementale, predizione.

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.optimizers import Adam
from config import HISTORY_LENGTH, FEATURE_COLS, BATCH_SIZE, PRETRAINED_MODEL_PATH
from utils import generate_labels
import logging

logger = logging.getLogger("bot_logger")

def create_baseline_model():
    """
    Crea un modello baseline LSTM con due layer.
    """
    model = Sequential()
    model.add(LSTM(units=128, return_sequences=True, input_shape=(HISTORY_LENGTH, len(FEATURE_COLS))))
    model.add(LSTM(units=64))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=Adam(1e-3), loss='binary_crossentropy', metrics=['accuracy'])
    return model

def load_pretrained_model():
    """
    Carica un modello pre-addestrato da PRETRAINED_MODEL_PATH se disponibile,
    altrimenti crea un baseline model.
    """
    try:
        model = load_model(PRETRAINED_MODEL_PATH)
        logger.info("Loaded pretrained model from model.h5")
        return model
    except:
        logger.info("No pretrained model found, using baseline model.")
        return create_baseline_model()

def train_model(model, data_buffer):
    """
    Training incrementale su ultimi BATCH_SIZE campioni.
    """
    X = np.array([data_buffer[i-HISTORY_LENGTH:i] for i in range(HISTORY_LENGTH, len(data_buffer))])
    y = generate_labels(data_buffer)
    if len(y) < BATCH_SIZE:
        return model
    X_train = X[-BATCH_SIZE:]
    y_train = y[-BATCH_SIZE:]
    model.fit(X_train, y_train, epochs=1, verbose=0)
    return model

def predict(model, data_buffer):
    """
    Predizione: Ritorna probabilità che il prezzo salga in FUTURE_STEPS step.
    """
    current_state = np.array(data_buffer[-HISTORY_LENGTH:]).reshape((1, HISTORY_LENGTH, len(FEATURE_COLS)))
    pred = model.predict(current_state)[0][0]
    return pred
