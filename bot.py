import asyncio
import aiohttp
from message import Message
from bs4 import BeautifulSoup

class Bot:

    def __init__(self, token):
        self._token = token
        self._api_url = 'https://api.telegram.org/bot{}/'.format(self._token)

    async def get_updates(self, queue, offset=None, timeout=0):
        method = 'getUpdates'
        params = {'offset': offset, 'timeout': timeout}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self._api_url + method, 
                params=params
            ) as resp:
                response = await resp.json()
        updates = response.get('result', [])
        if updates:
            for update in updates:
                await queue.put(Message(update))

    async def send_message(self, chat_id, text, reply_id=None):
        params = {
            'chat_id': chat_id,
            'text': text,
            'reply_to_message_id': reply_id
        }
        method = 'sendMessage'
        async with aiohttp.ClientSession() as session:
            await session.post(self._api_url + method, json=params)

    async def send_photo(self, chat_id, photo_url):
        params = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        method = 'sendPhoto'
        async with aiohttp.ClientSession() as session:
            await session.post(self._api_url + method, json=params)

    async def set_chat_title(self, chat_id, title):
        params = {
            'chat_id': chat_id,
            'title': title
        }
        method = 'setChatTitle'
        async with aiohttp.ClientSession() as session:
            await session.post(self._api_url + method, json=params)