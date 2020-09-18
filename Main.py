import json
import requests
import datetime
import ConfBot as Bot
import weather_driver
import covid_driver
import anekdot_driver

with open('config.json') as config_file:
    config = json.load(config_file)

bot_name = config['bot_name']
token = config['token']
group_id = config['group_id']
supergroup_id = config['supergroup_id']
my_id = config['my_id']

bot_help = '1. /episode <Название эпизода>\n' \
    'Установить новый эпизод, пишите только название\n\n' \
    '2. /episode_edit <Название эпизода>\n' \
    'Редактировать название текущего эпизода\n\n' \
    '3. /episode_num <Номер эпизода>\n' \
    'Показать название N эпизода\n\n' \
    '4. /weather{}\n' \
    'Показать погоду в Москве\n\n' \
    '5. /anekdot{}\n' \
    'Рассказать Дрону анекдот\n\n' \
    '6. /covid{}\n' \
    'Показать статистику по COVID-19 в России' \
    .format(bot_name, bot_name, bot_name)

bot = Bot.Bot(token)


def common_compare(last_chat_id, last_chat_text, last_type):
    anekdot = '/anekdot'
    covid = '/covid'
    weather = '/weather'
    if last_type == 'group' or last_type == 'supergroup':
        anekdot = anekdot + bot_name
        covid = covid + bot_name
        weather = weather + bot_name
    if last_chat_text == anekdot:
        bot.send_message(last_chat_id, '@Naravir, для тебя:\n\n{}'
                         .format(anekdot_driver.get_anekdot()))
    if last_chat_text == weather:
        weather = weather_driver.get_weather()
        bot.send_message(last_chat_id, weather)
    if last_chat_text == covid:
        covid_info = covid_driver.get_covid()
        covid_text = 'Коронавирус в России:\n\n' \
                     'Новые случаи: {}\n' \
                     'Всего случаев: {}\n\n' \
                     'Новых излечившихся: {}\n' \
                     'Всего излечившихся: {}\n\n' \
                     'Новые погибшие: {}\n' \
                     'Всего погибших: {}' \
                     .format(covid_info[0], covid_info[1], 
                             covid_info[2], covid_info[3],
                             covid_info[4], covid_info[5])
        bot.send_message(last_chat_id, covid_text)    


def group_compare(last_chat_id, last_chat_text, last_update):
    if last_chat_text == '/help{}'.format(bot_name):
        bot.send_message(last_chat_id, bot_help)
    if last_chat_text.lower().startswith('/episode_num '):
        bot.send_message(last_chat_id,
                         bot.get_chat_title(last_chat_text.lower()[13:]))
    elif last_chat_text.lower().startswith('/episode_edit '):
        bot.edit_chat_title(last_chat_id, last_chat_text[14:])
    elif last_chat_text.lower().startswith('/episode '):
        bot.set_chat_title(last_chat_id, last_chat_text[9:])


def private_compare(last_chat_text, last_update):
    if last_chat_text.startswith('/mail'):
        bot.send_mailing(last_update, group_id, last_chat_text[6:])


def main():

    new_offset = None
    timeout = 60
    # now = datetime.datetime.now()
    # today = now.day
    # hour = now.hour

    while True:

        # Send every day greetings
        # if today == now.day and hour == 10:
        #     bot.greetings(group_id)
        #     today = (datetime.date.today() + datetime.timedelta(days=1)).day

        # now = datetime.datetime.now()
        last_update = bot.last_update(new_offset, timeout)

        if last_update != 'error':
            last_update_id = last_update['update_id']
            try:
                # Get last update parameters
                last_chat_id = bot.get_chat_id(last_update)
                last_chat_text = bot.get_chat_text(last_update)
                last_type = bot.get_type(last_update)
                # Private or group chat
                common_compare(last_chat_id, last_chat_text, last_type)
                # Private chat
                if last_type == 'private':
                    private_compare(last_chat_text, last_update)
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