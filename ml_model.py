# ml_model.py
# Gestione modello ML: caricamento, training incrementale, predizioni

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM
from config import HISTORY_LENGTH, FEATURE_COLS, BATCH_SIZE, PRETRAINED_MODEL_PATH
from utils import generate_labels

def create_baseline_model():
    model = Sequential()
    model.add(LSTM(units=64, input_shape=(HISTORY_LENGTH, len(FEATURE_COLS))))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def load_pretrained_model():
    try:
        model = load_model(PRETRAINED_MODEL_PATH)
        return model
    except:
        return create_baseline_model()

def train_model(model, data_buffer):
    X = np.array([data_buffer[i-HISTORY_LENGTH:i] for i in range(HISTORY_LENGTH, len(data_buffer))])
    y = generate_labels(data_buffer)
    if len(y) < BATCH_SIZE:
        return model
    X_train = X[-BATCH_SIZE:]
    y_train = y[-BATCH_SIZE:]
    model.fit(X_train, y_train, epochs=1, verbose=0)
    return model

def predict(model, data_buffer):
    current_state = np.array(data_buffer[-HISTORY_LENGTH:]).reshape((1, HISTORY_LENGTH, len(FEATURE_COLS)))
    pred = model.predict(current_state)[0][0]
    return pred
