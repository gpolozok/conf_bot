import requests
from bs4 import BeautifulSoup

class Bot:

    def __init__(self, token):
        self.__token = token
        self.__api_url = 'https://api.telegram.org/bot{}/'.format(self.__token)

    def get_updates(self, offset=None, timeout=0):
        method = 'getUpdates'
        params = {'offset': offset, 'timeout': timeout}
        response = requests.get(self.__api_url + method, params)
        return response.json().get('result', [])

    def last_update(self, offset=None, timeout=0):
        result = self.get_updates(offset, timeout)
        if result:
            return result[-1]

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
        elif last_type == 'group' or last_type == 'supergroup':
            return last_update['message']['from']['first_name']

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
        params = {
            'chat_id': chat_id,
            'title': title
        }
        method = 'setChatTitle'
        response = requests.post(self.__api_url + method, params)
        return response