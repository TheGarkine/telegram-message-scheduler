import yaml
import os

class Database:
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            self.database = {
                'chats': {},
                'schedules': {}
            }
            self.save()
        with open(file_path, 'r', encoding="utf-8") as db_file:
            self.database = yaml.load(db_file, yaml.BaseLoader)
        self.chats = {}

    def save(self):
        with open(self.file_path, 'w', encoding="utf-8") as db_file:
            yaml.dump(self.database, db_file)

    def login(self, chat_id: int):
        if chat_id not in self.database['chats']:
            self.database['chats'][str(chat_id)] = { 'channels': []}
            self.save() 

    def is_logged_in(self, chat_id: int) -> bool:
        return str(chat_id) in self.database['chats']

    def subscribe(self, chat_id: int, channel: str):
        self.database['chats'][str(chat_id)]['channels'].append(channel)
        self.save()

    def unsubscribe(self, chat_id: int, channel: str):
        self.database['chats'][str(chat_id)]['channels'].remove(channel)
        self.save()

    def get_subscribed_chats(self, channel: str):
        return [int(chat_id) for chat_id in self.database['chats'] if channel in self.database['chats'][chat_id]['channels']]

    def is_subscribed(self, chat_id: int, channel: str) -> bool:
        return channel in self.database['chats'][str(chat_id)]['channels']
    
    def schedule(self, message_id: str, channel_id: str, date: str, time: str):
        self.database['schedules'].append({ 'date': date, 'time': time, 'channel': channel_id, 'message': message_id })
        self.save()

    def get_schedules(self):
        return self.database['schedules']
    
    def remove_schedule(self, schedule: dict):
        self.database['schedules'].remove(schedule)
        self.save()