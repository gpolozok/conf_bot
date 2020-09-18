import requests
import re
import sqlite3
from bs4 import BeautifulSoup
import warnings
import functools
import datetime


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func


class Bot:

    def __init__(self, token):
        self.__token = token
        self.__api_url = 'https://api.telegram.org/bot{}/'.format(self.__token)
        self.__now = datetime.datetime.now()
        self.__weather_url = 'https://www.meteoservice.ru/weather/now/moskva'
        self.__covid_url = 'https://api.covid19api.com/summary'
        self.__anecdor_url = 'https://anekdot-z.ru/random-anekdot'

    @deprecated
    def create_db(self):
        conn = sqlite3.connect('bot_bd.db')
        c = conn.cursor()
        c.execute('CREATE TABLE "episodes" '
                  '("NUMBER"    INTEGER NOT NULL UNIQUE, '
                  '"NAME"       TEXT NOT NULL UNIQUE);')
        conn.commit()
        c.close()

    def get_updates(self, offset=None, timeout=0):
        method = 'getUpdates'
        params = {'offset': offset, 'timeout': timeout}
        response = requests.get(self.__api_url + method, params)
        return response.json()['result']

    def last_update(self, offset=None, timeout=0):
        result = self.get_updates(offset, timeout)
        if(len(result) > 0):
            return result[-1]
        else:
            return 'error'

    def get_chat_id(self, last_update):
        return last_update['message']['chat']['id']

    def get_message_id(self, last_update):
        return last_update['message']['message_id']

    def get_chat_text(self, last_update):
        return last_update['message']['text']

    def get_type(self, last_update):
        return last_update['message']['chat']['type']

    def get_chat_name(self, last_update, last_type):
        if last_type == 'private':
            return last_update['message']['chat']['first_name']
        elif last_type == 'group':
            return last_update['message']['from']['first_name']

    def send_mailing(self, last_update, chat_id, text):
        if last_update['message']['chat']['username'] == 'grisha1505':
            params = {
                'chat_id': chat_id,
                'text': text
            }
            method = 'sendMessage'
            response = requests.post(self.__api_url + method, params)
            return response

    def send_message(self, chat_id, text, reply_id=None):
        params = {
            'chat_id': chat_id,
            'text': text,
            'reply_to_message_id': reply_id
        }
        method = 'sendMessage'
        response = requests.post(self.__api_url + method, params)
        return response

    def send_photo(self, chat_id, photo_url):
        params = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        method = 'sendPhoto'
        response = requests.post(self.__api_url + method, params)
        return response

    def set_chat_title(self, chat_id, title):
        conn = sqlite3.connect('bot_bd.db')
        c = conn.cursor()
        c.execute('SELECT NUMBER FROM episodes ORDER BY NUMBER DESC LIMIT 1;')
        episode_number = c.fetchone()[0]
        params = {
            'chat_id': chat_id,
            'title': 'Эпизод {}: {}'.format(episode_number + 1, title)
        }
        method = 'setChatTitle'
        c.execute('INSERT INTO episodes VALUES (\'{}\', \'{}\');'
                  .format(episode_number + 1, title))
        conn.commit()
        conn.close()
        response = requests.post(self.__api_url + method, params)
        return response

    def edit_chat_title(self, chat_id, title):
        conn = sqlite3.connect('bot_bd.db')
        c = conn.cursor()
        c.execute('SELECT NUMBER FROM episodes ORDER BY NUMBER DESC LIMIT 1;')
        episode_number = c.fetchone()[0]
        c.execute('UPDATE episodes SET NAME="{}" WHERE NUMBER = '
                  '(SELECT MAX(NUMBER) FROM episodes)'.format(title))
        params = {
            'chat_id': chat_id,
            'title': 'Эпизод {}: {}'.format(episode_number, title)
        }
        method = 'setChatTitle'
        conn.commit()
        conn.close()
        response = requests.post(self.__api_url + method, params)
        return response       

    def get_chat_title(self, episode_number):
        try:
            if(int(episode_number) <= 61):
                return "Я знаю историю только с 62 эпизода, сорян :("
            conn = sqlite3.connect('bot_bd.db')
            c = conn.cursor()
            c.execute('SELECT NUMBER FROM episodes '
                      'ORDER BY NUMBER DESC LIMIT 1;')
            last_episode = c.fetchone()[0]
            if last_episode < int(episode_number):
                last_chat_title = 'Такого эпизода еще не было'
            else:
                c.execute('SELECT NAME FROM episodes WHERE NUMBER == {};'
                          .format(episode_number))
                last_chat_title = 'Эпизод {}: {}'\
                    .format(episode_number, c.fetchone()[0])
            c.close()
        except ValueError:
            last_chat_title = 'Хорошая попытка, но надо ввести номер ' \
                'эпизода. Попытайся еще раз - я верю, у тебя все получится!'
            pass
        return last_chat_title

    def get_weather(self):
        webpage_response = requests.get(self.__weather_url)
        webpage = webpage_response.content
        soup = BeautifulSoup(webpage, 'html.parser')
        # get weather description
        mydivs = soup.findAll("div",
                              class_="small-12 medium-6 large-7 columns text-center")
        regex = re.compile(r'>(.*)<')
        weather = str(regex.findall(str(mydivs[0])))[2:-2]
        # get temperature
        mydivs = soup.findAll("div", class_="temperature")
        regex = re.compile(r'e">(.*)<')
        temperature = str(regex.findall(repr(mydivs)))[2:-2]
        return '''Температура за бортом: {}\n{}'''.format(temperature, weather)

    def get_covid(self):
        response = requests.get(self.__covid_url)
        info = response.json()['Countries']
        return (info[139]['NewConfirmed'], info[139]['TotalConfirmed'],
                info[139]['NewRecovered'], info[139]['TotalRecovered'],
                info[139]['NewDeaths'], info[139]['TotalDeaths'])

    def get_anekdot(self):
        webpage_response = requests.get(self.__anecdor_url)
        webpage = webpage_response.content
        soup = BeautifulSoup(webpage, 'html.parser')
        mydivs = soup.findAll('div', class_ = 'anekdot-content')
        anekdot = re.sub(r'</span><br/><span>', '\n', str(mydivs))
        anekdot = re.sub(r'[<>[\]abcdefghijklmnopqrstuvwxyz"=/_]', '', anekdot)
        return anekdot

    def greetings(self, group_id):
        weather = self.get_weather()
        greetings = 'Доброе утро, господа!\n\n' \
            '{}\n\n' \
            'Желаю всем удачного дня!\n\n{}' \
            .format(weather, str(self.__now)[:-7])
        self.send_message(group_id, greetings)