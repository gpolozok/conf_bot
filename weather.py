import aiohttp
from bs4 import BeautifulSoup

weather_url = 'https://www.meteoservice.ru/weather/now/moskva'


async def get_weather():
    async with aiohttp.ClientSession() as session:
        async with session.get(weather_url) as webpage_response:
            webpage = await webpage_response.read()

    soup = BeautifulSoup(webpage, 'html.parser')

    # get temperature
    mydivs = soup.find('span', attrs={'class': 'value'})
    temperature = mydivs.text

    # get weather description
    mydivs = soup.find('p', attrs={'class': 'margin-bottom-0'})
    weather = mydivs.text

    # get atmosphere pressure
    mydivs = soup.find('div', attrs={'class': 'h6 nospace-bottom'})
    pressure = mydivs.text

    return 'Температура за бортом: {}\n{}\n'\
        'Атм. давление: {}'\
        .format(temperature, weather, pressure.lstrip())
