import requests
from bs4 import BeautifulSoup

anekdot_url = 'https://anekdot-z.ru/random-anekdot'


def get_anekdot():
    webpage_response = requests.get(anekdot_url)
    webpage = webpage_response.content
    soup = BeautifulSoup(webpage, 'html.parser')
    mydivs = soup.find('div', attrs={'class': 'anekdot-content'})
    anekdot = mydivs.text
    return anekdot
