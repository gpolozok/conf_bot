import requests
from message import Message
from bs4 import BeautifulSoup

class Bot:

    def __init__(self, token):
        self._token = token
        self._api_url = 'https://api.telegram.org/bot{}/'.format(self._token)

    def get_updates(self, offset=None, timeout=0):
        method = 'getUpdates'
        params = {'offset': offset, 'timeout': timeout}
        response = requests.get(self._api_url + method, params)
        updates = response.json().get('result', [])
        return (Message(update) for update in updates)

    def send_message(self, chat_id, text, reply_id=None):
        params = {
            'chat_id': chat_id,
            'text': text,
            'reply_to_message_id': reply_id
        }
        method = 'sendMessage'
        response = requests.post(self._api_url + method, params)
        return response

    def send_photo(self, chat_id, photo_url):
        params = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        method = 'sendPhoto'
        response = requests.post(self._api_url + method, params)
        return response

    def set_chat_title(self, chat_id, title):
        params = {
            'chat_id': chat_id,
            'title': title
        }
        method = 'setChatTitle'
        response = requests.post(self._api_url + method, params)
        return response