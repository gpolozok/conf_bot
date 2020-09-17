import config
import ConfBot as Bot
import requests
import sqlite3
import datetime

vanga_pic_url = 'https://s.gorodche.ru/localStorage/news/73' \
    '/f8/40/8c/73f8408c_resizedScaled_1020to574.jpg'

group_id = config.group_id
supergroup_id = config.supergroup_id
my_id = config.my_id

greetings = ('привет', 'здравствуй', 'здравствуйте',
             'hello', 'здарова', 'здорова')

bot_help = '1. /episode <Название эпизода>\n' \
    'Установить новый эпизод, пишите только название\n\n' \
    '2. /episode_edit <Название эпизода>\n' \
    'Редактировать название текущего эпизода\n\n' \
    '3. /episode_num <Номер эпизода>\n' \
    'Показать название N эпизода\n\n' \
    '4. /weather\n' \
    'Показать погоду в Москве\n\n' \
    '5. /covid\n' \
    'Показать статистику по COVID-19 в России'

bot = Bot.Bot(config.token)


def common_compare(last_chat_id, last_chat_text):
    if last_chat_text.lower() == '/weather':
        weather = bot.get_weather()
        bot.send_message(last_chat_id, weather)
    if last_chat_text.lower() == '/covid':
        covid_info = bot.get_covid()
        covid_text = 'Коронавирус в России:\n\n' \
                     'Новые случаи: +{}\n' \
                     'Всего случаев: {}\n\n' \
                     'Новые погибшие: +{}\n' \
                     'Всего погибших: {}' \
                     .format(covid_info[0], covid_info[1], 
                     covid_info[2], covid_info[3])
        bot.send_message(last_chat_id, covid_text)    


def group_compare(last_chat_id, last_chat_text, last_update):
    if last_chat_text.lower() == '/help':
        bot.send_message(last_chat_id, bot_help)
    if last_chat_text.lower().startswith('/episode_num '):
        bot.send_message(last_chat_id,
                         bot.get_chat_title(last_chat_text.lower()[13:]))
    elif last_chat_text.lower().startswith('/episode_edit '):
        bot.edit_chat_title(last_chat_id, last_chat_text[14:])
    elif last_chat_text.lower().startswith('/episode '):
        bot.set_chat_title(last_chat_id, last_chat_text[9:])


def private_compare(last_chat_id, last_chat_text,
                    last_chat_name, last_update):
    if last_chat_text.lower() in greetings:
        bot.send_message(last_chat_id, 'Привет, твоё имя - {}!'
                         .format(last_chat_name))
        bot.send_photo(last_chat_id, vanga_pic_url)
    if last_chat_text.lower().startswith('/mail'):
        bot.send_mailing(last_update, group_id,
                         last_chat_text.lower()[6:])


def main():

    new_offset = None
    timeout = 60
    now = datetime.datetime.now()
    today = now.day
    hour = now.hour

    while True:

        # Send every day greetings
        if today == now.day and hour == 0:
            bot.greetings(group_id)
            today = (datetime.date.today() + datetime.timedelta(days=1)).day

        now = datetime.datetime.now()
        last_update = bot.last_update(new_offset, timeout)

        if last_update != 'error':
            last_update_id = last_update['update_id']
            try:
                # Get last update parameters
                last_chat_id = bot.get_chat_id(last_update)
                last_chat_text = bot.get_chat_text(last_update)
                last_type = bot.get_type(last_update)
                last_chat_name = bot.get_chat_name(last_update, last_type)
                # Private or group chat
                common_compare(last_chat_id, last_chat_text)
                # Private chat
                if last_type == 'private':
                    private_compare(last_chat_id, last_chat_text,
                                    last_chat_name, last_update)
                # Group or supergroup chat
                elif last_type == 'group' or last_type == 'supergroup':
                    group_compare(last_chat_id, last_chat_text, last_update)
            except KeyError:
                pass
        try:
            new_offset = last_update_id + 1
        except UnboundLocalError:
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
