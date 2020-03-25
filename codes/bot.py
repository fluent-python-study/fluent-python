import os
import json
import sqlite3
import subprocess
import bot_config
from slacker import Slacker
from websocket import create_connection


class BotDB:
    def __init__(self):
        self.__total_members = 5
        self.__members = ['luna', 'jason', 'eric', 'jinny', 'joel']
        self.__db_name = bot_config.SLACK_BOT_CONFIG['db']

        # initialize db related variables
        self.__con = sqlite3.connect(self.__db_name)
        self.__cur = self.__con.cursor()

        # querries
        self.__insert_sql = 'INSERT INTO presentations VALUES (?, ?)'
        self.__select_max = 'SELECT no FROM presentations ORDER BY no DESC LIMIT 1'
        self.__select_dones = 'SELCT name FROM presentations WHERE no BETWEEN ? AND ?'

    def get_max_num(self):
        result = self.select(self.__select_max, [])
        return result.pop()

    def get_dones(self, start_num, end_num):
        return self.select(self.__select_dones, [start_num, end_num])

    def insert(self, insert_sql, parameters):
        self.__cur.execute(insert_sql, parameters)
        self.__con.commit()

    def select(self, select_sql, parameters):
        self.__cur.execute(select_sql, parameters)
        return self.__cur.fetchall()

    def __del__(self):
        self.__con.close()


class Bot:
    def __init__(self, slacker):
        self._slacker = slacker
        resp = slacker.rtm.start()
        self._socket = create_connection(resp.body['url'])
        bot_user_id = slacker.users.get_user_id('monitor-bot')
        self._bot_id = '<@{}>'.format(bot_user_id)
        print('Successful bot initializing...')
        self.__db = BotDB()
        print('DB object created')

    def run_loop(self):
        print('Start event loop...')
        while True:
            ch, msg, target = self._read()
            print(ch, msg, target)
            if msg == '!발제자' or '발제자!':
                print('Set command')
                self._command = target
                msg = '실행할 명령어는 "{0}"입니다.'.format(target)
            self._send(ch, msg)

    def _read(self):
        while True:
            event = json.loads(self._socket.recv())
            if 'bot_id' in event and event.get('username') != 'testuser':
                continue
            ch, msg, target = self._parse(event)
            print(ch, msg, target)
            if not ch or not msg:
                continue
            break

        return ch, msg, target

    def _parse(self, event):
        if event['type'] != 'message' or\
                not event.get('text') or\
                self._bot_id not in event.get('text'):
            return None, None, None

        text = event['text'].replace(self._bot_id, '').strip()

        if text.startswith('/command'):
            text = text.strip().split()
            text, target = text[0], ' '.join(text[1:])
        if text.startswith('/execute'):
            text, target = text, ''

        return event['channel'], text, target

    def _send(self, ch, msg):
        self._slacker.chat.post_message(ch, msg, as_user=True)


def create_bot():
    slack_token = bot_config.SLACK_BOT_CONFIG['api-token']
    return Bot(Slacker(slack_token))


def run():
    bot = create_bot()
    bot.run_loop()


if __name__ == '__main__':
    run()