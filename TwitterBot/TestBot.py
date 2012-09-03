# -*- coding:utf-8 -*-
import logging
import logging.handlers
import sys
import re
from multiprocessing import Process, Lock, Queue
import crondaemon
from BaseBot import BaseBot
import json

logger = logging.getLogger("Bot")

class TestBot(BaseBot):
    __test__ = False
    def __init__(self):
        super(TestBot, self).__init__(None, None, None, None)
        self._latest_id = None
        self.setup_logger()
        self.start()

    def start(self):
        import json
        import MockTweepy

        # API初期化
        api = MockTweepy.API()
        self.api = api

        #アカウント設定の読み込み
        self._name = self.api.me().screen_name
        self._re_reply_to_me = re.compile(r'^@%s' % self._name, re.IGNORECASE)

        #やりとりの設定
        self._queue = Queue()
        self._cron = crondaemon.crondaemon()
        self._reply_hooks = []
        self._reply_hook_id = 0
        self._cron_funcs = {}
        self._cron_id = 0

        # デバッグ用ユーザの設定
        self.user = MockTweepy.getUser('test')

        # メインループ
        self.on_start()

    def setup_logger(self):
        hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.DEBUG)

        # setup error output
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    def get_timestamp(self):
        return "%Y/%m/%d %H:%M:%S"

    def reply_to_bot(self, text):
        text = u'@' + self._name + u' ' + text
        latest_id = self.api.getLatestId()
        print latest_id
        status = self.api.getStatus(
            text = text,
            user = self.user,
            in_reply_to_status_id = latest_id)
        self.on_data(json.dumps(status))
        return self.api.user_timeline()
