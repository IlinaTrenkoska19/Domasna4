import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from locale import setlocale, LC_ALL


class DataExtractor:
    BASE_URL = "https://www.mse.mk/mk/stats/symbolhistory/kmb"

    def __init__(self, output_file):
        self.output_file = output_file

    def run(self):
        response = requests.get(self.BASE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        dropdown_menu = soup.select_one("select#Code")

        company_list = []

        if dropdown_menu:
            for option in dropdown_menu.find_all("option"):
                code = option.get("value")
                if self.validate_code(code):
                    company_list.append(code)

        self.write_to_csv(company_list)
        return company_list

    @staticmethod
    def validate_code(code):
        return code and code.strip() and code.isalpha()

    def write_to_csv(self, codes):
        pd.DataFrame({"CompanyCode": codes}).to_csv(self.output_file, index=False)



class HistoricalDataFetcher:
    DETAILS_URL = "https://www.mse.mk/mk/stats/symbolhistory/"

    def __init__(self, input_file):
        self.input_file = input_file

    def run(self):
        companies = self.load_company_data()
        for company in companies:
            self.download_historical_data(company)

    def load_company_data(self):
        df = pd.read_csv(self.input_file)
        return [{"code": code, "last_date": None} for code in df["CompanyCode"]]

    def download_historical_data(self, company):
        current_year = datetime.now().year
        for year in range(current_year, current_year - 10, -1):
            start_date, end_date = datetime(year, 1, 1), datetime(year, 12, 31)
            self.fetch_data_for_period(company, start_date, end_date)

    def fetch_data_for_period(self, company, start_date, end_date):
        payload = {
            "FromDate": start_date.strftime("%Y-%m-%d"),
            "ToDate": end_date.strftime("%Y-%m-%d"),
        }
        response = requests.post(self.DETAILS_URL + company["code"], data=payload)
        response.raise_for_status()
        self.process_table(BeautifulSoup(response.text, 'html.parser').select_one("table#resultsTable"), company)

    def process_table(self, table, company):
        if not table:
            return
        records = []

        # Додавање на податоци од табелата
        for row in table.select("tbody tr"):
            cols = row.select("td")
            if cols:
                high_price = self.safe_parse(cols[2].text)
                if high_price is None:
                    continue

                records.append({
                    "record_date": self.format_date(cols[0].text),
                    "last_price": self.safe_parse(cols[1].text),
                    "high_price": high_price,
                    "low_price": self.safe_parse(cols[3].text),
                    "avg_price": self.safe_parse(cols[4].text),
                    "percent_change": self.safe_parse(cols[5].text),
                    "volume": self.safe_parse(cols[6].text, True),
                    "turnover_best": self.safe_parse(cols[7].text, True),
                    "total_turnover": self.safe_parse(cols[8].text, True),
                })

        # Ако нема записи, врати се
        if not records:
            return

        # Осигурување дека секогаш има header
        self.write_to_csv(records, company["code"])

    @staticmethod
    def format_date(date_str):
        return datetime.strptime(date_str, "%d.%m.%Y").date()

    @staticmethod
    def safe_parse(value, is_int=False):
        setlocale(LC_ALL, "de_DE")
        try:
            return int(value.replace('.', '').replace(',', '')) if is_int else float(value.replace('.', '').replace(',', '.'))
        except ValueError:
            return None

    def write_to_csv(self, data, company_code):
        file_name = f"historical_data_{company_code}.csv"

        # Проверка дали датотеката е празна или не постои
        file_exists = os.path.exists(file_name)
        is_empty = False
        if file_exists:
            is_empty = os.path.getsize(file_name) == 0

        # Запишување на податоците со правилно управување на header
        pd.DataFrame(data).to_csv(
            file_name,
            mode='a',
            header=not file_exists or is_empty,  # Додај header ако датотеката не постои или е празна
            index=False
        )




class DataUpdater:
    DETAILS_URL = "https://www.mse.mk/mk/stats/symbolhistory/"

    def __init__(self, input_file):
        self.input_file = input_file

    def run(self):
        companies = self.load_company_data()
        for company in companies:
            self.update_missing_data(company)

    def load_company_data(self):
        df = pd.read_csv(self.input_file)
        return [{"code": code, "last_date": None} for code in df["CompanyCode"]]

    def update_missing_data(self, company):
        file_name = f"historical_data_{company['code']}.csv"
        if os.path.exists(file_name):
            last_date = self.get_last_recorded_date(file_name)
            if last_date:
                self.fetch_data_for_period(company, last_date, datetime.now())
        else:
            print(f"No data for {company['code']}. Fetching last 10 years.")
            current_year = datetime.now().year
            for year in range(current_year, current_year - 10, -1):
                start_date, end_date = datetime(year, 1, 1), datetime(year, 12, 31)
                self.fetch_data_for_period(company, start_date, end_date)

    def get_last_recorded_date(self, file_name):
        df = pd.read_csv(file_name)
        return pd.to_datetime(df["record_date"]).max() if not df.empty else None

    def fetch_data_for_period(self, company, start_date, end_date):
        payload = {
            "FromDate": start_date.strftime("%Y-%m-%d"),
            "ToDate": end_date.strftime("%Y-%m-%d"),
        }
        response = requests.post(self.DETAILS_URL + company["code"], data=payload)
        response.raise_for_status()
        self.process_table(BeautifulSoup(response.text, 'html.parser').select_one("table#resultsTable"), company)

    def process_table(self, table, company):
        if not table:
            return
        records = []

        # Додавање на податоци од табелата
        for row in table.select("tbody tr"):
            cols = row.select("td")
            if cols:
                high_price = self.safe_parse(cols[2].text)
                if high_price is None:
                    continue

                records.append({
                    "record_date": self.format_date(cols[0].text),
                    "last_price": self.safe_parse(cols[1].text),
                    "high_price": high_price,
                    "low_price": self.safe_parse(cols[3].text),
                    "avg_price": self.safe_parse(cols[4].text),
                    "percent_change": self.safe_parse(cols[5].text),
                    "volume": self.safe_parse(cols[6].text, True),
                    "turnover_best": self.safe_parse(cols[7].text, True),
                    "total_turnover": self.safe_parse(cols[8].text, True),
                })

        # Ако нема записи, врати се
        if not records:
            return

        # Осигурување дека секогаш има header
        self.write_to_csv(records, company["code"])

    def write_to_csv(self, data, company_code):
        file_name = f"historical_data_{company_code}.csv"

        # Проверка дали датотеката е празна или не постои
        file_exists = os.path.exists(file_name)
        is_empty = False
        if file_exists:
            is_empty = os.path.getsize(file_name) == 0

        # Запишување на податоците со правилно управување на header
        pd.DataFrame(data).to_csv(
            file_name,
            mode='a',
            header=not file_exists or is_empty,  # Додај header ако датотеката не постои или е празна
            index=False
        )



if __name__ == "__main__":
    extractor = DataExtractor("issuers.csv")
    codes = extractor.run()

    fetcher = HistoricalDataFetcher("issuers.csv")
    fetcher.run()

    updater = DataUpdater("issuers.csv")
    updater.run()
