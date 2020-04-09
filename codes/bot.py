import os
import copy
import json
import random
import sqlite3
import subprocess
import bot_config
from slacker import Slacker
from websocket import create_connection


class BotDB:
    def __init__(self):
        self.__db_name = bot_config.SLACK_BOT_CONFIG['db']

        # initialize db related variables
        self.__con = sqlite3.connect(self.__db_name)
        self.__cur = self.__con.cursor()

        # querries
        self.__insert_sql = 'INSERT INTO presentations VALUES (?, ?)'
        self.__select_max = 'SELECT no FROM presentations ORDER BY no DESC LIMIT 1'
        self.__select_dones = 'SELECT name FROM presentations WHERE no BETWEEN ? AND ?'

    def get_max_num(self):
        result = self.select(self.__select_max, [])
        return result.pop()[0]

    def get_dones(self, start_num, end_num):
        return self.select(self.__select_dones, [start_num, end_num])

    def insert_next(self, no, name):
        self.insert(self.__insert_sql, [no, name])

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
        bot_user_id = slacker.users.get_user_id(bot_config.SLACK_BOT_CONFIG['bot_user_id'])
        self._bot_id = '<@{}>'.format(bot_user_id)
        print('Successful bot initializing...')

        self.__db = BotDB()
        print('DB object created')
        
        self.total_members = 5
        self.members = ['luna', 'jason', 'eric', 'jinny', 'joel']

    def __get_random(self):
        max_num = self.__db.get_max_num()
        rotation_num = max_num // self.total_members
        rotation_done_yn = max_num % self.total_members
        print('가장 큰 순번: {0}, 몫: {1}, 나머지: {2}'.format(max_num, rotation_num, rotation_done_yn))

        candidates = copy.deepcopy(self.members)
        print('후보: {0}'.format(candidates))

        # 나머지가 0일 경우 한 바퀴 다 돌았음을 의미함으로 다한 사람 filter할 필요 없음
        if rotation_done_yn:
            start_num = rotation_num * self.total_members + 1
            end_num = ((rotation_num + 1) * self.total_members) 
            dones = [i[0] for i in self.__db.get_dones(start_num, end_num)]
            print('발표한 사람: {0}'.format(dones))
            candidates = list(filter(lambda x: x not in dones, candidates))

        next_presentor = random.choice(candidates)
        print('최종 후보: {0}, 다음 순서: {1}'.format(candidates, next_presentor))

        # db에 업데이트
        self.__db.insert_next(max_num + 1, next_presentor)
        print('db updated')

        return next_presentor        

    def run_loop(self):
        print('Start event loop...')
        while True:
            ch, msg, target = self._read()
            print(ch, msg, target)
            if msg == '!발제자' or msg == '발제자!':
                next_presentor = self.__get_random()
                print('get next presentor')
                msg = '다음 발제자는 "{0}"입니다!!!>_<'.format(next_presentor)
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

        if text.startswith('!발제자') or text.startswith('발제자!'):
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