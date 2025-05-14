import requests
from bs4 import BeautifulSoup

class HospitalFinderAgent:
    def __init__(self, sources):
        self.sources = sources

    def fetch_sources(self):
        data = []
        for source in self.sources:
            response = requests.get(source)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                data += self.extract_info(soup)
        return data

    def extract_info(self, raw_data):
        articles = raw_data.find_all('article')
        new_hospitals = []
        for article in articles:
            if "new hospital" in article.text.lower():
                new_hospitals.append({
                    'name': article.find('h2').text.strip(),
                    'link': article.find('a')['href']
                })
        return new_hospitals
