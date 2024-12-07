import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

model = Sequential([
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])

print("TensorFlow funziona correttamente!")
