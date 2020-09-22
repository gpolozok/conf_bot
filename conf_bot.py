import json
import requests
import datetime
import sqlite3
from bot import Bot
import weather
import covid
import anekdot
from multiprocessing.dummy import Pool as ThreadPool

class ConfBot:

    def __init__(self):
        with open('config.json') as config_file:
            config = json.load(config_file)
        self.__bot_name = config['bot_name']
        self.__group_id = config['group_id']
        self.__supergroup_id = config['supergroup_id']
        self.__my_id = config['my_id']
        self.__bot = Bot(config['token'])

    @property
    def triggers(self):
        return {
            'help' : '/help{}'.format(self.__bot_name),
            'weather' : '/weather{}'.format(self.__bot_name),
            'covid' : '/covid{}'.format(self.__bot_name),
            'anekdot' : '/anekdot{}'.format(self.__bot_name),
            'episode' : '/ep',
            'episode_edit' : '/ep_edit',
            'episode_num' : '/ep_num'
        }
    

    def get_parameters(self, last_update):
        last_chat_id = self.__bot.get_chat_id(last_update)
        last_chat_text = self.__bot.get_chat_text(last_update)
        last_type = self.__bot.get_type(last_update)
        return {
            'id': last_chat_id, 
            'text': last_chat_text, 
            'type': last_type
        }

    def send_mailing(self, text, last_update):
        if last_update['message']['chat']['username'] == 'grisha1505':
            self.__bot.send_message(self.__group_id, text[6:])

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
            .format(n=self.__bot_name)
        self.__bot.send_message(chat_id, bot_help)

    def send_weather(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.__bot.send_message(chat_id, weather.get_weather())

    def send_covid(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.__bot.send_message(chat_id, covid.get_covid())

    def send_anekdot(self, **kwargs):
        chat_id = kwargs['chat_id']
        self.__bot.send_message(chat_id, anekdot.get_anekdot())

    def new_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            self.__bot.send_message(chat_id, 'Надо ввести название эпизода')
        else:
            conn = sqlite3.connect('bot_bd.db')
            c = conn.cursor()
            c.execute('SELECT NUMBER FROM episodes '\
                'ORDER BY NUMBER DESC LIMIT 1;')
            episode_number = c.fetchone()[0]
            new_title = 'Эпизод {}: {}'.format(episode_number + 1, title)
            c.execute('INSERT INTO episodes VALUES (\'{}\', \'{}\');'
                    .format(episode_number + 1, title))
            conn.commit()
            conn.close()
            self.__bot.set_chat_title(chat_id, new_title)

    def edit_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            self.__bot.send_message(chat_id, 'Надо ввести новое название')
        else:
            conn = sqlite3.connect('bot_bd.db')
            c = conn.cursor()
            c.execute('SELECT NUMBER FROM episodes '\
                'ORDER BY NUMBER DESC LIMIT 1;')
            episode_number = c.fetchone()[0]
            c.execute('UPDATE episodes SET NAME="{}" WHERE NUMBER = '
                    '(SELECT MAX(NUMBER) FROM episodes)'.format(title))
            new_title = 'Эпизод {}: {}'.format(episode_number, title)
            conn.commit()
            conn.close()
            self.__bot.set_chat_title(chat_id, new_title)

    def send_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        episode_number = kwargs['text']
        try:
            if(int(episode_number) <= 61):
                last_chat_title = 'Я знаю историю только с '\
                    '62 эпизода, сорян :('
            else:
                conn = sqlite3.connect('bot_bd.db')
                c = conn.cursor()
                c.execute('SELECT NUMBER FROM episodes '
                    'ORDER BY NUMBER DESC LIMIT 1;'
                )
                last_episode = c.fetchone()[0]
                if last_episode < int(episode_number):
                    last_chat_title = 'Такого эпизода еще не было'
                else:
                    c.execute('SELECT NAME FROM episodes WHERE NUMBER == {};'
                        .format(episode_number)
                    )
                    last_chat_title = 'Эпизод {}: {}'\
                        .format(episode_number, c.fetchone()[0])
                c.close()
        except ValueError:
            last_chat_title = 'Хорошая попытка, но надо ввести номер ' \
                'эпизода. Попытайся еще раз - я верю, у тебя все получится!'
            pass
        self.__bot.send_message(chat_id, last_chat_title)

    def compare(self, last_chat_id, last_chat_text, last_type, last_update):
        if last_type == 'private' and last_chat_text.startswith('/mail '):
            self.send_mailing(last_chat_text, last_update)
        elif last_type == 'group' or last_type == 'supergroup':
            self.command_handler(last_chat_id, last_chat_text) 

    def command_handler(self, last_chat_id, last_chat_text):
        triggers = self.triggers
        split = last_chat_text.split(" ", maxsplit=1)
        command, text = split if len(split) > 1 else (split[0], None)
        command_trigger = {
            triggers.get('help') : self.send_help,
            triggers.get('weather') : self.send_weather,
            triggers.get('covid') : self.send_covid,
            triggers.get('anekdot') : self.send_anekdot,
            triggers.get('episode') : self.new_chat_title,
            triggers.get('episode_edit') : self.edit_chat_title,
            triggers.get('episode_num') : self.send_chat_title
        }

        if (trigger := command_trigger.get(command)) is not None:
            trigger(chat_id = last_chat_id, text = text)

    def greetings(self, today, group_id):
        now = datetime.datetime.now()
        hour = now.hour
        if today == now.day and hour == 8:
            weather_info = weather.get_weather()
            greetings = 'Доброе утро, господа!\n\n' \
                '{}\n' \
                'Желаю всем удачного дня!' \
                .format(weather_info)
            self.__bot.send_message(group_id, greetings)
        return (datetime.date.today() + datetime.timedelta(days=1)).day

    def update_handler(self, last_update):
        last_update_id = last_update['update_id']
        try:
            parameters = self.get_parameters(last_update)
            self.compare(
                parameters.get('id'), 
                parameters.get('text'), 
                parameters.get('type'),
                last_update
            )
        except KeyError:
            pass
        return last_update_id


    def main(self):

        new_offset = None
        timeout = 5
        now = datetime.datetime.now()
        today = now.day
        pool = ThreadPool(4)

        while True:

            today = self.greetings(today, self.__group_id)

            updates = self.__bot.get_updates(new_offset, timeout)
            offsets = pool.map(self.update_handler, updates)
            if offsets:
                new_offset = max(offsets) + 1


if __name__ == '__main__':
    confa_bot = ConfBot()
    try:
        confa_bot.main()
    except KeyboardInterrupt:
        exit()