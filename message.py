class Message:

    def __init__(self, update):
        self.update_id = update['update_id']
        self.message_id = update['message']['message_id']
        self.chat_text = update['message']['text']
        self.chat_id = update['message']['chat']['id']
        self.chat_type = update['message']['chat']['type']
        self.name = update['message']['from']['first_name']
        self.username = update['message']['from']['username']
        if self.chat_text.startswith('/'):
            split = self.chat_text.split(" ", maxsplit=1)
            self.command, self.text = split \
                if len(split) > 1 \
                else (split[0], None)
        else:
            self.command = None
            self.text = self.chat_text