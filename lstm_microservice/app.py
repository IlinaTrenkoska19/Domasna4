import os
import numpy as np
import pandas as pd
import requests
from flask import Flask, request, jsonify
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

app = Flask(__name__)

# Helper funkcija za pripremu podataka
def prepare_dataset(data, time_step=30):
    X, y = [], []
    for i in range(len(data) - time_step - 1):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)

# Функција за преземање на CSV фајлот преку HTTP барање
def download_csv(company_code):
    url = f'http://127.0.0.1:5000/get-csv/{company_code}'
    response = requests.get(url)

    if response.status_code == 200:
        file_path = f"historical_data_{company_code}.csv"
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    else:
        raise FileNotFoundError("Error fetching CSV file")

# API endpoint за LSTM прогноза
# API endpoint за LSTM прогноза
@app.route('/lstm-prediction', methods=['POST'])
def lstm_prediction():
    request_data = request.get_json()
    company_code = request_data.get('companyCode')

    # Преземи го CSV фајлот преку микросервис
    try:
        file_path = download_csv(company_code)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    # Учитување на податоците од CSV
    df = pd.read_csv(file_path)
    df['record_date'] = pd.to_datetime(df['record_date'], format='%Y-%m-%d')
    stock_data = df[['record_date', 'last_price']].set_index('record_date')

    # Скалирање на податоците
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(stock_data[['last_price']])

    # Поделба на тренинг и валидационен сет
    train_size = int(len(stock_data) * 0.7)
    train_set, val_set = scaled_data[:train_size], scaled_data[train_size:]

    # Подготовка на dataset за LSTM модел
    time_step = 30
    X_train, y_train = prepare_dataset(train_set, time_step)
    X_val, y_val = prepare_dataset(val_set, time_step)

    # Reshape податоци за LSTM
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_val = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)

    # Креирање на LSTM моделот
    model = Sequential([
        LSTM(units=100, return_sequences=True, input_shape=(X_train.shape[1], 1)),
        LSTM(units=100, return_sequences=False),
        Dense(units=1)
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    # Тренирање на моделот
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_val, y_val), verbose=1)

    # Прогноза
    latest_data = val_set[-time_step:].reshape(1, time_step, 1)
    prediction = model.predict(latest_data)
    predicted_price = scaler.inverse_transform(prediction)[0][0]

    return jsonify({"predicted_price": round(float(predicted_price), 2)})

# Стартување на Flask апликацијата
if __name__ == '__main__':
    app.run(port=5003, debug=True)