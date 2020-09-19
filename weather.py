import requests
import re
from bs4 import BeautifulSoup

weather_url = 'https://www.meteoservice.ru/weather/now/moskva'

def get_weather():
    webpage_response = requests.get(weather_url)
    webpage = webpage_response.content
    soup = BeautifulSoup(webpage, 'html.parser')

    # get weather description
    mydivs = soup.findAll(
        "div",
        class_="small-12 medium-6 large-7 columns text-center"
    )
    weather = str(re.findall(r'>(.*)<', str(mydivs[0])))[2:-2]

    # get temperature
    mydivs = soup.findAll("div", class_="temperature")
    temperature = str(re.findall(r'e">(.*)<', str(mydivs)))[2:-2]

    return 'Температура за бортом: {}\n{}'.format(temperature, weather)