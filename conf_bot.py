import json
import requests
import datetime
from bot import Bot
import weather
import covid
import anekdot

class ConfBot:

    def __init__(self):
        with open('config.json') as config_file:
            config = json.load(config_file)
        self.__bot_name = config['bot_name']
        self.__group_id = config['group_id']
        self.__supergroup_id = config['supergroup_id']
        self.__my_id = config['my_id']
        self.__bot = Bot(config['token'])

    def get_help(self):
        bot_help = '1. /episode <Название эпизода>\n' \
            'Установить новый эпизод, пишите только название\n\n' \
            '2. /episode_edit <Название эпизода>\n' \
            'Редактировать название текущего эпизода\n\n' \
            '3. /episode_num <Номер эпизода>\n' \
            'Показать название N эпизода\n\n' \
            '4. /weather{n}\n' \
            'Показать погоду в Москве\n\n' \
            '5. /anekdot{n}\n' \
            'Рассказать Дрону анекдот\n\n' \
            '6. /covid{n}\n' \
            'Показать статистику по COVID-19 в России' \
            .format(n=self.__bot_name)
        return bot_help

    def common_compare(self, last_chat_id, last_chat_text, last_type):
        anekdot_info = '/anekdot'
        covid_info = '/covid'
        weather_info = '/weather'
        if last_type == 'group' or last_type == 'supergroup':
            anekdot_info = anekdot_info + self.__bot_name
            covid_info = covid_info + self.__bot_name
            weather_info = weather_info + self.__bot_name
        if last_chat_text == anekdot_info:
            self.__bot.send_message(last_chat_id, '@Naravir, для тебя:\n\n{}'
                            .format(anekdot.get_anekdot()))
        if last_chat_text == weather_info:
            weather_info = weather.get_weather()
            self.__bot.send_message(last_chat_id, weather_info)
        if last_chat_text == covid_info:
            covid_info = covid.get_covid()
            self.__bot.send_message(last_chat_id, covid_info)    

    def group_compare(self, last_chat_id, last_chat_text, last_update):
        if last_chat_text == '/help{}'.format(self.__bot_name):
            self.__bot.send_message(last_chat_id, self.get_help())
        if last_chat_text.lower().startswith('/episode_num '):
            self.__bot.send_message(last_chat_id,
                self.__bot.get_chat_title(last_chat_text.lower()[13:]))
        elif last_chat_text.lower().startswith('/episode_edit '):
            self.__bot.edit_chat_title(last_chat_id, last_chat_text[14:])
        elif last_chat_text.lower().startswith('/episode '):
            self.__bot.set_chat_title(last_chat_id, last_chat_text[9:])


    def private_compare(self, last_chat_text, last_update):
        if last_chat_text.startswith('/mail'):
            self.__bot.send_mailing(last_update, 
                self.__group_id, last_chat_text[6:])

    def greetings(self, group_id):
        weather_info = weather.get_weather()
        greetings = 'Доброе утро, господа!\n\n' \
            '{}\n\n' \
            'Желаю всем удачного дня!' \
            .format(weather_info)
        self.__bot.send_message(group_id, greetings)

    def run(self):

        new_offset = None
        timeout = 60
        now = datetime.datetime.now()
        today = now.day
        hour = now.hour
        last_update_id = 0

        while True:

            # Send every day greetings
            if today == now.day and hour == 10:
                self.greetings(self.__group_id)
                today = (datetime.date.today() + datetime.timedelta(days=1)).day

            now = datetime.datetime.now()
            last_update = self.__bot.last_update(new_offset, timeout)

            if last_update != 'error':
                last_update_id = last_update['update_id']
                try:
                    # Get last update parameters
                    last_chat_id = self.__bot.get_chat_id(last_update)
                    last_chat_text = self.__bot.get_chat_text(last_update)
                    last_type = self.__bot.get_type(last_update)
                    # Private or group chat
                    self.common_compare(last_chat_id, last_chat_text, last_type)
                    # Private chat
                    if last_type == 'private':
                        self.private_compare(last_chat_text, last_update)
                    # Group or supergroup chat
                    elif last_type == 'group' or last_type == 'supergroup':
                        self.group_compare(last_chat_id, last_chat_text, last_update)
                except KeyError:
                    pass

            new_offset = last_update_id + 1


if __name__ == '__main__':
    confa_bot = ConfBot()
    try:
        confa_bot.run()
    except KeyboardInterrupt:
        exit()