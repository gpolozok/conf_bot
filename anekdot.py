import aiohttp
from bs4 import BeautifulSoup

anekdot_url = 'https://anekdot-z.ru/random-anekdot'


async def get_anekdot():
    async with aiohttp.ClientSession() as session:
        async with session.get(anekdot_url) as webpage_response:
            webpage = await webpage_response.read()

    soup = BeautifulSoup(webpage, 'html.parser')
    mydivs = soup.find('div', attrs={'class': 'anekdot-content'})
    anekdot = mydivs.text
    return anekdot
