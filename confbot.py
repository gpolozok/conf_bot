import datetime
import json
import asyncio
import sqlite3
import weather
import covid
import anekdot
from bot import Bot


class ConfBot:

    def __init__(self):
        with open('config.json') as config_file:
            config = json.load(config_file)
        self.bot_name = config['bot_name']
        self.group_id = config['group_id']
        self.supergroup_id = config['supergroup_id']
        self.my_id = config['my_id']
        self.bot = Bot(config['token'])
        self.workers_amount = config['workers_amount']

    @property
    def triggers(self):
        return {
            'help': '/help{}'.format(self.bot_name),
            'weather': '/weather{}'.format(self.bot_name),
            'covid': '/covid{}'.format(self.bot_name),
            'anekdot': '/anekdot{}'.format(self.bot_name),
            'episode': '/ep',
            'episode_edit': '/ep_edit',
            'episode_num': '/ep_num'
        }

    async def greetings(self):
        now = datetime.datetime.now()
        today = now.day
        while True:
            await asyncio.sleep(900)
            if today == now.day and now.hour == 8:
                weather_info = await weather.get_weather()
                greetings = 'Доброе утро, господа!\n\n' \
                    '{}\n' \
                    'Желаю всем удачного дня!' \
                    .format(weather_info)
                await self.bot.send_message(self.group_id, greetings)
                today = (datetime.date.today() + datetime.timedelta(days=1)) \
                    .day
            else:
                print(today)

    async def send_mailing(self, message):
        if message.username == 'grisha1505':
            await self.bot.send_message(self.group_id, message.text)

    async def send_help(self, **kwargs):
        chat_id = kwargs['chat_id']
        bot_help = '1. /ep <Название эпизода>\n' \
            'Установить новый эпизод, пишите только название\n\n' \
            '2. /ep_edit <Название эпизода>\n' \
            'Редактировать название текущего эпизода\n\n' \
            '3. /ep_num <Номер эпизода>\n' \
            'Показать название N эпизода\n\n' \
            '4. /weather{n}\n' \
            'Показать погоду в Москве\n\n' \
            '5. /anekdot{n}\n' \
            'Рассказать Дрону анекдот\n\n' \
            '6. /covid{n}\n' \
            'Показать статистику по COVID-19 в России' \
            .format(n=self.bot_name)
        await self.bot.send_message(chat_id, bot_help)

    async def send_weather(self, **kwargs):
        chat_id = kwargs['chat_id']
        await self.bot.send_message(chat_id, await weather.get_weather())

    async def send_covid(self, **kwargs):
        chat_id = kwargs['chat_id']
        await self.bot.send_message(chat_id, await covid.get_covid())

    async def send_anekdot(self, **kwargs):
        chat_id = kwargs['chat_id']
        await self.bot.send_message(chat_id, await anekdot.get_anekdot())

    async def new_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            await self.bot.send_message(chat_id, 'Надо ввести новое название')
        else:
            conn = sqlite3.connect('bot_bd.db')
            c = conn.cursor()
            c.execute(
                'SELECT NUMBER FROM episodes '
                'ORDER BY NUMBER DESC LIMIT 1;'
            )
            episode_number = c.fetchone()[0]
            new_title = 'Эпизод {}: {}'.format(episode_number + 1, title)
            c.execute(
                'INSERT INTO episodes VALUES (\'{}\', \'{}\');'
                .format(episode_number + 1, title)
            )
            conn.commit()
            conn.close()
            await self.bot.set_chat_title(chat_id, new_title)

    async def edit_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            await self.bot.send_message(chat_id, 'Надо ввести новое название')
        else:
            conn = sqlite3.connect('bot_bd.db')
            c = conn.cursor()
            c.execute(
                'SELECT NUMBER FROM episodes '
                'ORDER BY NUMBER DESC LIMIT 1;'
            )
            episode_number = c.fetchone()[0]
            c.execute(
                'UPDATE episodes SET NAME="{}" WHERE NUMBER = '
                '(SELECT MAX(NUMBER) FROM episodes)'.format(title)
            )
            new_title = 'Эпизод {}: {}'.format(episode_number, title)
            conn.commit()
            conn.close()
            await self.bot.set_chat_title(chat_id, new_title)

    async def get_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        episode_number = kwargs['text']
        try:
            if episode_number is None:
                chat_title = 'Надо ввести номер эпизода'
            elif int(episode_number) <= 61:
                chat_title = 'Я знаю историю только с '\
                    '62 эпизода, сорян :('
            else:
                conn = sqlite3.connect('bot_bd.db')
                c = conn.cursor()
                c.execute(
                    'SELECT NUMBER FROM episodes '
                    'ORDER BY NUMBER DESC LIMIT 1;'
                )
                episode = c.fetchone()[0]
                if episode < int(episode_number):
                    chat_title = 'Такого эпизода еще не было'
                else:
                    c.execute(
                        'SELECT NAME FROM episodes WHERE NUMBER == {};'
                        .format(episode_number)
                    )
                    chat_title = 'Эпизод {}: {}'\
                        .format(episode_number, c.fetchone()[0])
                c.close()
        except ValueError:
            chat_title = 'Хорошая попытка, но надо ввести номер ' \
                'эпизода. Попытайся еще раз - я верю, у тебя все получится!'
            pass
        await self.bot.send_message(chat_id, chat_title)

    async def compare(self, message):
        if message.chat_type == 'private' and message.command == '/mail':
            await self.send_mailing(message)
        elif message.chat_type in ['group', 'supergroup']:
            await self.command_handler(message)

    async def command_handler(self, message):
        triggers = self.triggers
        command_trigger = {
            triggers.get('help'): self.send_help,
            triggers.get('weather'): self.send_weather,
            triggers.get('covid'): self.send_covid,
            triggers.get('anekdot'): self.send_anekdot,
            triggers.get('episode'): self.new_chat_title,
            triggers.get('episode_edit'): self.edit_chat_title,
            triggers.get('episode_num'): self.get_chat_title
        }

        if (trigger := command_trigger.get(message.command)) is not None:
            await trigger(chat_id=message.chat_id, text=message.text)

    async def update_handler(self, queue):
        while True:
            message = await queue.get()
            await self.compare(message)

    def main(self):

        timeout = 60
        queue = asyncio.Queue()

        loop = asyncio.get_event_loop()
        loop.create_task(self.greetings())
        loop.create_task(self.bot.get_updates(queue, timeout))
        for _ in range(self.workers_amount):
            loop.create_task(self.update_handler(queue))
        loop.run_forever()


if __name__ == '__main__':
    confbot = ConfBot()

    try:
        confbot.main()
    except Exception:
        print('Fail')
