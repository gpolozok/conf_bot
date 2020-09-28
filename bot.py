import aiohttp
from message import Message


class Bot:

    def __init__(self, token):
        self._token = token
        self._api_url = 'https://api.telegram.org/bot{}/'.format(self._token)

    async def get_updates(self, queue, timeout=0):
        offset = 0
        while True:
            method = 'getUpdates'
            params = {'offset': offset, 'timeout': timeout}
            updates = []
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._api_url + method,
                    params=params
                ) as resp:
                    updates = (await resp.json()).get('result', [])
            offset_list = []
            for update in updates:
                message = Message(update)
                offset_list.append(message.update_id)
                queue.put_nowait(message)
            offset = max(offset_list) + 1 if offset_list else offset

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
