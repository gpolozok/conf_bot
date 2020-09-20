import requests
import re
from bs4 import BeautifulSoup

anecdot_url = 'https://anekdot-z.ru/random-anekdot'

def get_anekdot():
    webpage_response = requests.get(anecdot_url)
    webpage = webpage_response.content
    soup = BeautifulSoup(webpage, 'html.parser')
    mydivs = soup.findAll('div', class_ = 'anekdot-content')
    anekdot = re.sub(r'-content', '', str(mydivs))
    anekdot = re.sub(r'<br/>', '\n', anekdot)
    anekdot = re.sub(r'[abcdefghijklmnopqrstuvwxyz_[\]/<>="\']', '', anekdot)
    return anekdot