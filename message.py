class Message:

    def __init__(self, update):
        self.update_id = update.get('update_id')
        if update.get('message') is not None:
            message = update.get('message')
        else:
            message = update.get('edited_message')
        self.message_id = message.get('message_id')
        self.chat_text = message.get('text')
        self.chat_id = message['chat']['id']
        self.chat_type = message['chat']['type']
        self.name = message['from']['first_name']
        self.username = message['from']['username']
        if self.chat_text is not None and self.chat_text.startswith('/'):
            split = self.chat_text.split(" ", maxsplit=1)
            self.command, self.text = split \
                if len(split) > 1 \
                else (split[0], None)
        else:
            self.command = None
            self.text = self.chat_text
