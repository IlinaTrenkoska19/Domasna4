import os
import pandas as pd
from flask import Flask, request, jsonify
import ta
import requests

# Flask апликација
app = Flask(__name__)

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

# Ендпоинт за техничка анализа
@app.route('/technical-analysis', methods=['POST'])
def perform_technical_analysis():
    company_code = request.json.get('companyCode')
    if not company_code:
        return jsonify({"error": "Company code is required."}), 400

    # Преземи го CSV фајлот преку микросервис
    try:
        file_path = download_csv(company_code)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    # Учитување на податоците од CSV
    try:
        data = pd.read_csv(file_path, parse_dates=['record_date'])
        data.set_index('record_date', inplace=True)

        # Пресметка на техничките индикатори
        data['SMA_10'] = ta.trend.sma_indicator(data['last_price'], window=10)
        data['EMA_10'] = ta.trend.ema_indicator(data['last_price'], window=10)
        data['RSI'] = ta.momentum.rsi(data['last_price'], window=14)
        data['MACD'] = ta.trend.macd(data['last_price'])
        data['MACD_signal'] = ta.trend.macd_signal(data['last_price'])
        data['MACD_hist'] = ta.trend.macd_diff(data['last_price'])
        data['Stochastic_K'] = ta.momentum.stoch(data['high_price'], data['low_price'], data['last_price'], window=14)
        data['Stochastic_D'] = ta.momentum.stoch_signal(data['high_price'], data['low_price'], data['last_price'], window=14)
        data['CCI'] = ta.trend.cci(data['high_price'], data['low_price'], data['last_price'], window=14)
        data['ROC'] = ta.momentum.roc(data['last_price'], window=10)

        # Креирање на цели за идни цени
        data['Future_Price_1D'] = data['last_price'].shift(-1)
        data['Future_Price_1W'] = data['last_price'].shift(-5)
        data['Future_Price_1M'] = data['last_price'].shift(-20)

        # Дефинирање на цели (Buy: 1, Sell: -1, Hold: 0)
        for period, shift in [('1D', 'Future_Price_1D'), ('1W', 'Future_Price_1W'), ('1M', 'Future_Price_1M')]:
            data[f'Target_{period}'] = (
                (data[shift] > data['last_price']).astype(int)
                - (data[shift] < data['last_price']).astype(int)
            )

        data.dropna(subset=['Target_1D', 'Target_1W', 'Target_1M'], inplace=True)

        # Избор на карактеристики
        feature_columns = ['SMA_10', 'EMA_10', 'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
                           'Stochastic_K', 'Stochastic_D', 'CCI', 'ROC']
        X = data[feature_columns]

        # Тренинг и предвидување за секој временски период
        prediction_results = {}
        for period in ['1D', '1W', '1M']:
            y = data[f'Target_{period}']
            latest_data = X.iloc[-1].values.reshape(1, -1)
            predicted_signal = y.iloc[1]  # За пример, користиме последната вредност како резултат

            prediction_results[f'predicted_signal_{period}'] = (
                "BUY" if predicted_signal == 1 else "SELL" if predicted_signal == -1 else "HOLD"
            )

        return jsonify(prediction_results)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
