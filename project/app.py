import csv
import os

import matplotlib
import numpy as np
import pandas as pd
import requests
import ta
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify,send_file
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import Sequential
from textblob import TextBlob

matplotlib.use('Agg')

import matplotlib.pyplot as plt

app = Flask(__name__)


def read_company_codes():
    company_codes = []
    with open('issuers.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            company_codes.append(row[0])
    return company_codes


def read_historical_data(company_code):
    file_path = os.path.join(os.getcwd(), f'historical_data_{company_code}.csv')
    data = []

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    else:
        print(f"CSV file for {company_code} does not exist.")

    return data


@app.route('/')
def home():
    company_codes = read_company_codes()
    return render_template('index.html', company_codes=company_codes)


@app.route('/company', methods=['POST'])
def company_data():
    company_code = request.form.get('company')
    historical_data = read_historical_data(company_code)
    return render_template('kompanija.html', company_code=company_code, historical_data=historical_data)


@app.route('/technical-analysis', methods=['POST'])
def perform_technical_analysis():
    company_code = request.form.get('companyCode')

    # Send request to the microservice for technical analysis
    try:
        response = requests.post('http://127.0.0.1:5001/technical-analysis', json={'companyCode': company_code})
        if response.status_code == 200:
            # If successful, return the result from the microservice
            prediction_results = response.json()
            return jsonify(prediction_results)
        else:
            return jsonify({"error": "Error from microservice: " + response.text}), 500
    except requests.RequestException as e:
        return jsonify({"error": f"Error connecting to microservice: {str(e)}"}), 500



@app.route('/fundamental-analysis', methods=['POST'])
def fundamental_analysis():
    company_code = request.form.get('companyCode')  # Uzimamo companyCode iz forme

    # Ja povikuvame funkcijata koja prakja baranje za mikroservisot
    recommendation = get_fundamental_analysis_from_microservice(company_code)

    # Vrakjame rezultat na korisnikot preku HTML
    return render_template('fundamental_analysis_result.html', recommendation=recommendation)

@app.route('/lstm', methods=['POST'])
def lstm_prediction():
    company_code = request.form.get('companyCode')

    if not company_code:
        return jsonify({"error": "Company code is required"}), 400

    predicted_price = get_lstm_prediction_from_microservice(company_code)

    return jsonify({"predicted_price": predicted_price})

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Process the form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # For now, print the data (replace with your own logic like sending an email)
        print(f"Contact form submitted: Name={name}, Email={email}, Message={message}")
        return render_template('contact.html', success=True)
    return render_template('contact.html', success=False)


def get_fundamental_analysis_from_microservice(company_code):
    # URL na mikroservisot (pretpostavuvame deka raboti na porta 5002)
    url = 'http://127.0.0.1:5002/fundamental-analysis'

    # Podatocite koi gi prakjame na mikroservisot
    data = {'companyCode': company_code}

    try:
        # Prakjanje POST baranje
        response = requests.post(url, json=data)

        # Ako mikroservisot vrati status 200 (uspeshno)
        if response.status_code == 200:
            result = response.json()  # Odgovor od mikroservisot vo JSON format
            return result.get('recommendation', 'No recommendation')
        else:
            return f"Error from microservice: {response.text}"

    except requests.RequestException as e:
        return f"Error connecting to microservice: {str(e)}"


def get_lstm_prediction_from_microservice(company_code):
    url = 'http://127.0.0.1:5003/lstm-prediction'
    data = {'companyCode': company_code}

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get('predicted_price', 'No prediction')
        else:
            return f"Error from microservice: {response.text}"
    except requests.RequestException as e:
        return f"Error connecting to microservice: {str(e)}"

# Route за преземање на CSV фајл
# @app.route('/get-csv/<company_code>', methods=['GET'])
# def get_csv(company_code):
#     file_path = f"project/historical_data_{company_code}.csv"
#     try:
#         return send_file(file_path)
#     except FileNotFoundError:
#         return {"error": "CSV file not found"}, 404


@app.route('/get-csv/<company_code>', methods=['GET'])
def get_csv(company_code):
    # Креирај целосен пат до фајлот
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Папката каде се наоѓа `app.py`
    file_path = os.path.join(base_dir, f"historical_data_{company_code}.csv")

    # Логирање за дебагирање
    print(f"Checking for file at: {file_path}")

    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": f"CSV file not found at {file_path}"}), 404

if __name__ == '__main__':
    app.run(debug=True)
