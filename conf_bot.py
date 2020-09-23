import json
import requests
import datetime
import sqlite3
import weather
import covid
import anekdot
from bot import Bot
from message import Message
from multiprocessing.dummy import Pool as ThreadPool

class ConfBot:

    def __init__(self):
        with open('config.json') as config_file:
            config = json.load(config_file)
        self.bot_name = config['bot_name']
        self.group_id = config['group_id']
        self.supergroup_id = config['supergroup_id']
        self.my_id = config['my_id']
        self.bot = Bot(config['token'])

    @property
    def triggers(self):
        return {
            'help' : '/help{}'.format(self.bot_name),
            'weather' : '/weather{}'.format(self.bot_name),
            'covid' : '/covid{}'.format(self.bot_name),
            'anekdot' : '/anekdot{}'.format(self.bot_name),
            'episode' : '/ep',
            'episode_edit' : '/ep_edit',
            'episode_num' : '/ep_num'
        }

    def send_mailing(self, text, username):
        if username == 'grisha1505':
            self.bot.send_message(self.group_id, text)

    def send_help(self, **kwargs):
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
        self.bot.send_message(chat_id, bot_help)

    def send_weather(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.bot.send_message(chat_id, weather.get_weather())

    def send_covid(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.bot.send_message(chat_id, covid.get_covid())

    def send_anekdot(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.bot.send_message(chat_id, anekdot.get_anekdot())

    def new_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            self.bot.send_message(chat_id, 'Надо ввести название эпизода')
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
            self.bot.set_chat_title(chat_id, new_title)

    def edit_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            self.bot.send_message(chat_id, 'Надо ввести новое название')
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
            self.bot.set_chat_title(chat_id, new_title)

    def get_chat_title(self, **kwargs):
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
        self.bot.send_message(chat_id, chat_title)

    def compare(self, chat_id, chat_type, username, command, text):
        if chat_type == 'private' and command.startswith('/mail '):
            self.send_mailing(text, username)
        elif chat_type == 'group' or chat_type == 'supergroup':
            self.command_handler(chat_id, command, text) 

    def command_handler(self, chat_id, command, text):
        triggers = self.triggers
        command_trigger = {
            triggers.get('help') : self.send_help,
            triggers.get('weather') : self.send_weather,
            triggers.get('covid') : self.send_covid,
            triggers.get('anekdot') : self.send_anekdot,
            triggers.get('episode') : self.new_chat_title,
            triggers.get('episode_edit') : self.edit_chat_title,
            triggers.get('episode_num') : self.get_chat_title
        }

        if (trigger := command_trigger.get(command)) is not None:
            trigger(chat_id = chat_id, text = text)

    def greetings(self, today, group_id):
        now = datetime.datetime.now()
        hour = now.hour
        if today == now.day and hour == 8:
            weather_info = weather.get_weather()
            greetings = 'Доброе утро, господа!\n\n' \
                '{}\n' \
                'Желаю всем удачного дня!' \
                .format(weather_info)
            self.bot.send_message(group_id, greetings)
        return (datetime.date.today() + datetime.timedelta(days=1)).day

    def update_handler(self, message):
        try:
            self.compare(
                message.chat_id,
                message.chat_type,
                message.username,
                message.command,
                message.text,
            )
        except KeyError:
            pass
        return message.update_id


    def main(self):

        new_offset = None
        timeout = 60
        now = datetime.datetime.now()
        today = now.day
        pool = ThreadPool(4)

        while True:

            today = self.greetings(today, self.group_id)

            offsets = pool.map(
                self.update_handler, 
                self.bot.get_updates(new_offset, timeout)
            )
            if offsets:
                new_offset = max(offsets) + 1


if __name__ == '__main__':
    confabot = ConfBot()
    try:
        confabot.main()
    except KeyboardInterrupt:
        exit()