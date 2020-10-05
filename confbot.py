import datetime
import json
import asyncio
import asyncpg
import weather
import covid
import anekdot
import conflict_help as ch
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
        self.db_name = config['db_name']
        self.db_host = config['db_host']
        self.db_port = config['db_port']
        self.db_user = config['db_user']
        self.db_pass = config['db_pass']

    @property
    def triggers(self):
        return {
            'nhelp': '/help{}'.format(self.bot_name),
            'nweather': '/weather{}'.format(self.bot_name),
            'ncovid': '/covid{}'.format(self.bot_name),
            'nanekdot': '/anekdot{}'.format(self.bot_name),
            'nepisode': '/ep{}'.format(self.bot_name),
            'nepisode_edit': '/ep_edit{}'.format(self.bot_name),
            'nepisode_num': '/ep_num{}'.format(self.bot_name),
            'nnew_conflict': '/conflict{}'.format(self.bot_name),
            'nend_conflict': '/conflict_end{}'.format(self.bot_name),
            'nconflict_info': '/conflict_info{}'.format(self.bot_name),
            'nconflict_help': '/conflict_help{}'.format(self.bot_name),
            'help': '/help',
            'weather': '/weather',
            'covid': '/covid',
            'anekdot': '/anekdot',
            'episode': '/ep',
            'episode_edit': '/ep_edit',
            'episode_num': '/ep_num',
            'new_conflict': '/conflict',
            'end_conflict': '/conflict_end',
            'conflict_info': '/conflict_info',
            'conflict_help': '/conflict_help'
        }

    async def db_connection(self):
        return await asyncpg.connect(
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            database=self.db_name
        )

    async def get_greetings(self, now):
        now_month = now.strftime('%m')
        now_day = now.strftime('%d')
        conn = await self.db_connection()
        sql = 'SELECT firstname, username FROM confbot.persons ' \
            'WHERE (SELECT EXTRACT(DAY FROM birthdate)) = ($1) ' \
            'AND (SELECT EXTRACT(MONTH FROM birthdate)) = ($2)'
        data = (int(now_day), int(now_month))
        bdboy = await conn.fetchrow(sql, *data)
        if bdboy:
            return 'Доброе утро, господа!\n\n' \
                'Cегодня особенный день - наш добрый друг {} ' \
                'отмечает свой День Рождения!\n\n' \
                '{}, бот поздравляет тебя и желает ' \
                'счастья, любви и процветания!\n\n{}' \
                .format(
                    bdboy[0],
                    bdboy[1],
                    await weather.get_weather()
                )
        sql = 'SELECT firstname, username, companion FROM confbot.persons ' \
            'WHERE (SELECT EXTRACT(DAY FROM compbirthdate)) = ($1) ' \
            'AND (SELECT EXTRACT(MONTH FROM compbirthdate)) = ($2)'
        bdboy = await conn.fetchrow(sql, *data)
        if bdboy:
            return 'Доброе утро, господа!\n\n' \
                'Cегодня особенный день - {}, '\
                'девушка, которой посвятил жизнь {}, ' \
                'отмечает свой День Рождения!\n\n' \
                '{}, бот поздравляет твою спутницу c этим ' \
                'знаменательным днем и желает ' \
                'счастья, любви и процветания!\n\n{}' \
                .format(
                    bdboy[2],
                    bdboy[0],
                    bdboy[1],
                    await weather.get_weather()
                )
        else:
            return None

    async def greetings(self):
        now = datetime.datetime.now()
        today = now.day
        while True:
            await asyncio.sleep(900)
            now = datetime.datetime.now()
            greetings = await self.get_greetings(now)
            if greetings is None:
                greetings = 'Доброе утро, господа!\n\n' \
                    '{}\n' \
                    'Желаю всем удачного дня!' \
                    .format(await weather.get_weather())
            if today == now.day and now.hour == 8:
                await self.bot.send_message(self.group_id, greetings)
                today = (datetime.date.today() + datetime.timedelta(days=1)) \
                    .day

    async def send_mailing(self, message):
        if message.username == 'grisha1505':
            await self.bot.send_message(self.supergroup_id, message.text)

    async def send_help(self, **kwargs):
        chat_id = kwargs['chat_id']
        bot_help = '1. /ep <Название эпизода>\n' \
            'Установить новый эпизод, пишите только название\n\n' \
            '2. /ep_edit <Название эпизода>\n' \
            'Редактировать название текущего эпизода\n\n' \
            '3. /ep_num <Номер эпизода>\n' \
            'Показать название N эпизода (min - 47)\n\n' \
            '4. /weather\n' \
            'Показать погоду в Москве\n\n' \
            '5. /anekdot\n' \
            'Рассказать Дрону анекдот\n\n' \
            '6. /covid\n' \
            'Показать статистику по COVID-19 в России\n\n' \
            '7. /conflict_help\n' \
            'Показать инструкцию по конфликтам'
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
            conn = await self.db_connection()
            episode_number = (await conn.fetchrow(
                'SELECT episode_num FROM confbot.episodes WHERE id = '
                '(SELECT MAX(id) FROM confbot.episodes)'
            ))[0]
            sql = 'INSERT INTO confbot.episodes (episode_num, title) ' \
                'VALUES (($1), ($2));'
            data = (episode_number + 1, title)
            await conn.execute(sql, *data)
            await conn.close()
            message = 'Эпизод {}: {}'.format(episode_number + 1, title)
            await self.bot.set_chat_title(chat_id, message)

    async def edit_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        title = kwargs['text']
        if title is None:
            await self.bot.send_message(chat_id, 'Надо ввести новое название')
        else:
            conn = await self.db_connection()
            episode_number = (await conn.fetchrow(
                'SELECT episode_num FROM confbot.episodes '
                'WHERE id = (SELECT MAX(id) FROM confbot.episodes)'
            ))[0]
            await conn.execute(
                'UPDATE confbot.episodes '
                'SET title=\'{}\' WHERE episode_num={}'
                .format(title, episode_number)
            )
            sql = 'UPDATE confbot.episodes ' \
                'SET title=($1) WHERE episode_num=($2)'
            data = (title, episode_number)
            await conn.execute(sql, *data)
            await conn.close()
            message = 'Эпизод {}: {}'.format(episode_number, title)
            await self.bot.set_chat_title(chat_id, message)

    async def get_chat_title(self, **kwargs):
        chat_id = kwargs['chat_id']
        episode_number = kwargs['text']
        try:
            if episode_number is None:
                chat_title = 'Надо ввести номер эпизода'
            elif int(episode_number) < 47:
                chat_title = 'Я знаю историю только с 47 эпизода, сорян :('
            else:
                conn = await self.db_connection()
                episode = (await conn.fetchrow(
                    'SELECT episode_num FROM confbot.episodes WHERE id = '
                    '(SELECT MAX(id) FROM confbot.episodes)'
                ))[0]
                if int(episode_number) > episode:
                    chat_title = 'Такого эпизода еще не было'
                else:
                    SQL = 'SELECT title FROM confbot.episodes ' \
                        'WHERE episode_num = ($1);'
                    data = int(episode_number)
                    title = (await conn.fetchrow(SQL, data))[0]
                    chat_title = 'Эпизод {}: {}'\
                        .format(episode_number, title)
                await conn.close()
        except ValueError:
            chat_title = 'Хорошая попытка, но надо ввести номер ' \
                'эпизода. Попытайся еще раз - я верю, у тебя все получится!'
            pass
        await self.bot.send_message(chat_id, chat_title)

    async def new_conflict(self, **kwargs):
        chat_id = kwargs['chat_id']
        plaintiff_id = kwargs['user_id']
        text = kwargs['text']
        if text is None:
            message = 'Введите username того, кому хотите объявит конфликт'
            return await self.bot.send_message(chat_id, message)
        split = (kwargs['text']).split(" ", maxsplit=1)
        defendant_username, reason = split \
            if len(split) > 1 \
            else (split[0], 'Отсутствует')
        conn = await self.db_connection()
        sql = 'SELECT user_id FROM confbot.persons WHERE username = ($1)'
        defendant_id = await conn.fetchrow(sql, defendant_username)
        if defendant_id is None:
            message = 'Такого username в конфе нет'
        elif defendant_id[0] == plaintiff_id:
            message = 'Нельзя конфликтовать с самим собой'
        else:
            sql = 'INSERT INTO confbot.conflicts ' \
                '(user1_id, user2_id, reason, solved) ' \
                'VALUES (($1), ($2), ($3), FALSE);'
            data = (plaintiff_id, defendant_id[0], reason)
            await conn.execute(sql, *data)
            sql = 'SELECT username FROM confbot.persons ' \
                'WHERE user_id = ($1)'
            data = plaintiff_id
            plaintiff_username = (await conn.fetchrow(sql, data))[0]
            sql = 'SELECT MAX(id) from confbot.conflicts'
            conflict_id = (await conn.fetchrow(sql))[0]
            message = 'Внимание! ' \
                'Между {} и {} назрел конфликт!\n\n' \
                'Причина: {}\n\n' \
                'id конфликта: {}' \
                .format(
                    plaintiff_username,
                    defendant_username,
                    reason,
                    conflict_id)
        await conn.close()
        await self.bot.send_message(chat_id, message)

    async def finisher_check(self, conn, user_id, conflict_id):
        user_id = user_id
        sql = 'SELECT user1_id FROM confbot.conflicts WHERE id = ($1)'
        plaintiff_id = (await conn.fetchrow(sql, conflict_id))
        if plaintiff_id is not None:
            return user_id == plaintiff_id[0]
        else:
            return False

    async def end_conflict(self, **kwargs):
        chat_id = kwargs['chat_id']
        text = kwargs['text']
        user_id = kwargs['user_id']
        if text is None:
            message = 'Введите id решенного конфликта'
            return await self.bot.send_message(chat_id, message)
        try:
            conn = await self.db_connection()
            if await self.finisher_check(conn, user_id, int(text)):
                sql = 'UPDATE confbot.conflicts SET solved=TRUE ' \
                    'WHERE id = ($1)'
                await conn.execute(sql, int(text))
                sql = 'SELECT username FROM confbot.persons ' \
                    'WHERE user_id = ($1)'
                plaintiff = (await conn.fetchrow(sql, user_id))[0]
                sql = 'SELECT username FROM confbot.persons WHERE ' \
                    'user_id = (SELECT user2_id FROM confbot.conflicts ' \
                    'WHERE id = ($1))'
                defendant = (await conn.fetchrow(sql, int(text)))[0]
                message = 'Решен конфликт №{} между {} и {}' \
                    .format(text, plaintiff, defendant)
            else:
                sql = 'SELECT username FROM confbot.persons ' \
                    'WHERE user_id = (SELECT user1_id from ' \
                    'confbot.conflicts WHERE id = ($1))'
                username = (await conn.fetchrow(sql, int(text)))
                if username is not None:
                    message = 'Не вы начали этот конфликт, завершить его ' \
                        'может только {}'.format(username[0])
                else:
                    message = 'Конфликта с таким id нет'
        except ValueError:
            message = 'Введите корректный id'
        await conn.close()
        await self.bot.send_message(chat_id, message)

    async def conflict_id_info(self, conn, conflict):
        sql = 'SELECT username from confbot.persons WHERE user_id = ($1)'
        plaintiff = (await conn.fetchrow(sql, conflict['user1_id']))[0]
        defendant = (await conn.fetchrow(sql, conflict['user2_id']))[0]
        reason = conflict['reason']
        status = 'решен' if conflict['solved'] else 'не решен'
        return 'Конфликт №{}\n' \
            'Объявил конфликт: {}\n' \
            'Принял конфликт: {}\n' \
            'Причина: {}\n' \
            'Статус: {}' \
            .format(conflict['id'], plaintiff, defendant, reason, status)

    async def conflict_user_info(self, conn, username):
        unsolved = 0
        accept_info = 'Принял конфликты: '
        declare_info = 'Объявил конфликты: '
        sql = 'SELECT id from confbot.conflicts WHERE ' \
            'user2_id = (SELECT user_id from confbot.persons ' \
            'WHERE username = ($1)) AND solved = FALSE'
        accept_ids = await conn.fetch(sql, username)
        for accept_id in accept_ids:
            unsolved += 1
            accept_info = accept_info + str(accept_id[0]) + ' '
        sql = 'SELECT id from confbot.conflicts WHERE ' \
            'user1_id = (SELECT user_id from confbot.persons ' \
            'WHERE username = ($1)) AND solved = FALSE'
        declare_ids = await conn.fetch(sql, username)
        for declare_id in declare_ids:
            unsolved += 1
            declare_info = declare_info + str(declare_id[0]) + ' '
        sql = 'SELECT COUNT(*) FROM confbot.conflicts WHERE (' \
            ' user1_id = (SELECT user_id FROM confbot.persons ' \
            'WHERE username = ($1)) ' \
            'OR user2_id = (SELECT user_id FROM confbot.persons '\
            'WHERE username = ($1))) ' \
            'AND solved = true'
        solved = (await conn.fetchrow(sql, username))[0]
        solved_info = 'Решенных конфликтов: {}'.format(solved)
        unsolved_info = 'Нерешенных конфликтов: {}'.format(unsolved)
        return 'Конфликты {}\n{}\n{}\n{}\n{}' \
            .format(
                username,
                solved_info,
                unsolved_info,
                declare_info,
                accept_info
            )

    async def conflict_info(self, **kwargs):
        chat_id = kwargs['chat_id']
        text = kwargs['text']
        if text is None:
            message = 'Введите username или id конфликта'
            return await self.bot.send_message(chat_id, message)
        conn = await self.db_connection()
        try:
            sql = 'SELECT * FROM confbot.conflicts WHERE id = ($1)'
            info = await conn.fetchrow(sql, int(text))
            if info is None:
                message = 'Конфликта с таким id не существует'
            else:
                message = await self.conflict_id_info(conn, info)
        except ValueError:
            sql = 'SELECT user_id FROM confbot.persons WHERE username = ($1)'
            info = await conn.fetchrow(sql, text)
            if info is None:
                message = 'Введите корректный username или id конфликта'
            else:
                message = await self.conflict_user_info(conn, text)
        await conn.close()
        await self.bot.send_message(chat_id, message)

    async def conflict_help(self, **kwargs):
        chat_id = kwargs['chat_id']
        return await self.bot.send_message(chat_id, ch.conflict_help)

    async def command_handler(self, message):
        triggers = self.triggers
        command_trigger = {
            triggers.get('help'): self.send_help,
            triggers.get('weather'): self.send_weather,
            triggers.get('covid'): self.send_covid,
            triggers.get('anekdot'): self.send_anekdot,
            triggers.get('episode'): self.new_chat_title,
            triggers.get('episode_edit'): self.edit_chat_title,
            triggers.get('episode_num'): self.get_chat_title,
            triggers.get('new_conflict'): self.new_conflict,
            triggers.get('end_conflict'): self.end_conflict,
            triggers.get('conflict_info'): self.conflict_info,
            triggers.get('conflict_help'): self.conflict_help,
            triggers.get('nhelp'): self.send_help,
            triggers.get('nweather'): self.send_weather,
            triggers.get('ncovid'): self.send_covid,
            triggers.get('nanekdot'): self.send_anekdot,
            triggers.get('nepisode'): self.new_chat_title,
            triggers.get('nepisode_edit'): self.edit_chat_title,
            triggers.get('nepisode_num'): self.get_chat_title,
            triggers.get('nnew_conflict'): self.new_conflict,
            triggers.get('nend_conflict'): self.end_conflict,
            triggers.get('nconflict_info'): self.conflict_info,
            triggers.get('nconflict_help'): self.conflict_help
        }
        if (trigger := command_trigger.get(message.command)) is not None:
            await trigger(
                chat_id=message.chat_id,
                user_id=message.user_id,
                text=message.text
            )

    async def compare(self, message):
        if message.chat_type == 'private' and message.command == '/mail':
            await self.send_mailing(message)
        elif message.chat_type in ['group', 'supergroup']:
            await self.command_handler(message)

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
    except Exception as ex:
        print('Fail\n{}'.format(ex))
