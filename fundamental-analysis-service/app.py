import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from textblob import TextBlob

app = Flask(__name__)

@app.route('/fundamental-analysis', methods=['POST'])
def fundamental_analysis():
    # Примање на companyCode од барањето
    company_code = request.json.get('companyCode')

    base_url = "https://www.mse.mk"
    company_url = f"{base_url}/mk/symbol/{company_code}"

    try:
        # Прашуваме за податоци од веб-страницата на компанијата
        response = requests.get(company_url)
        response.raise_for_status()
    except requests.RequestException:
        return jsonify({"error": "Failed to retrieve company data."}), 500

    soup = BeautifulSoup(response.content, 'html.parser')
    news_section = soup.find('div', id='seiNetIssuerLatestNews')

    if not news_section:
        return jsonify({"error": "No news available for this company."}), 404

    news_links = news_section.find_all('a', href=True)

    total_sentiment = 0
    article_count = 0

    for news in news_links:
        news_url = news['href']
        if not news_url.startswith("http"):
            news_url = base_url + news_url

        try:
            news_response = requests.get(news_url)
            news_response.raise_for_status()
        except requests.RequestException:
            continue

        news_soup = BeautifulSoup(news_response.content, 'html.parser')
        news_text = news_soup.get_text()

        sentiment = TextBlob(news_text).sentiment.polarity
        total_sentiment += sentiment
        article_count += 1

    if article_count == 0:
        return jsonify({"error": "No relevant news found."}), 404

    # Пресметување на просечен сентимент
    average_sentiment = total_sentiment / article_count
    recommendation = "Buy stocks" if average_sentiment > 0 else "Sell stocks"

    return jsonify({"recommendation": recommendation})

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Портата 5002 за микросервисот
