#!/usr/bin/env python
# -*- coding:utf-8 -*-

import tweepy
import tweepywrap
import time
import re
import codecs
import sys
import datetime
import crondaemon
import logging
import logging.handlers
from multiprocessing import Process, Lock, Queue

logger = logging.getLogger("BaseBot")

class BotShutdown(Exception):
    """ボットをシャットダウンしたいときに投げる例外"""
    pass

def StreamProcess(queue, consumer_key, consumer_secret, access_key, access_secret):
    """ユーザストリームプロセスの実行内容"""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    stream = tweepy.Stream(auth, BotStream(queue))
    logger.info('User Stream Starting...')
    stream.userstream(async=False)

class BotStream(tweepywrap.StreamListener):
    """ユーザーストリームのリスナ"""
    def __init__(self, queue):
        super(BotStream, self).__init__()
        self.queue = queue

    def on_data(self, data):
        """メインプロセスへ通知"""
        self.queue.put(('stream', data))
        
class BaseBot(tweepywrap.StreamListener):
    def __init__(self, consumer_key, consumer_secret, access_key, access_secret):
        super(BaseBot, self).__init__()
        #API設定
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_key = access_key
        self._access_secret = access_secret
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_key, access_secret)
        self.api = tweepy.API(self.auth, retry_count=10, retry_delay=1)

        #アカウント設定の読み込み
        self._name = self.api.me().screen_name
        self._re_reply_to_me = re.compile(r'^@%s' % self._name, re.IGNORECASE)

        #やりとりの設定
        self._queue = Queue()
        self._cron = crondaemon.crondaemon()
        self._reply_hooks = []
        self._cron_funcs = {}
        self._cron_id = 0

    def setup_logger(self, opts):
        # setup output
        if opts.log:
            hdlr = logging.FileHandler(opts.log, 'a')
        else:
            hdlr = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
        if opts.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        # setup error output
        hdlr = logging.StreamHandler()
        hdlr.setLevel(logging.ERROR)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    def setup_optparser(self):
        from optparse import OptionParser, OptionGroup
        usage = 'usage: %prog [options] command'
        parser = OptionParser(usage=usage)
        parser.add_option('-l', '--log',
                          dest='log',
                          default='',
                          help="Filename for log output",
                          )
        parser.add_option('-d', '--debug',
                          dest='debug',
                          action='store_true',
                          default=False,
                          help="Enable debug output",
                          )
        group = OptionGroup(parser, "command",
                            "something else..."
                            )
        parser.add_option_group(group)
        return parser

    def main(self):
        parser = self.setup_optparser()
        options, args = parser.parse_args(sys.argv)
        self.setup_logger(options)
        self.start()

    def start(self):
        """ボットの動作を開始する"""

        #ユーザストリームを別プロセスで開始
        args = (self._queue, self._consumer_key, self._consumer_secret, self._access_key, self._access_secret)
        streaming_process = Process(target=StreamProcess, args = args)
        streaming_process.daemon = True
        streaming_process.start()
        
        #cronサービスを開始
        logger.info(u'Cron Daemon Starting...')
        self._cron.start(async=True)

        self.on_start()

        while True:
            try:
                data_type, data = self._queue.get()
                if data_type=='stream':
                    self.on_data(data)
                elif data_type=='cron':
                    self._cron_funcs[data]()
            except BotShutdown, e:
                logger.warning('Shutdown Message Received')
                break
            except KeyboardInterrupt, e:
                logger.warning('Keyboard Interrupt')
                break
            except Exception, e:
                logger.error(str(e))

        try:
            self.on_shutdown()
        except Exception, e:
            logger.error(str(e))
        
        self._cron.stop()
        logger.info(u'Shutdown')

    def on_start(self):
        pass

    def on_shutdown(self):
        pass

    def append_reply_hook(self, func):
        """リプライフックを追加する"""
        self._reply_hooks.append(func)

    def append_cron(self, crontime, func, args=(), kargs={}):
        """定期実行タスクを追加する"""
        cron_id = u'cron-' + str(self._cron_id)
        self._cron_id += 1

        def wrap():
            logger.info(u'Running ' + cron_id)
            func(self, *args, **kargs)

        def put():
            self._queue.put(('cron', cron_id))

        self._cron_funcs[cron_id] = wrap
        self._cron.append(crontime, put)

    def on_status(self, status):
        """ステータス取得"""
        if self._re_reply_to_me.search(status.text):
            for func in self._reply_hooks:
                ret = func(self, status)
                if ret:
                    break

    def update_status(self, status, *args, **kargs):
        logger.info('update:' + status)
        self.api.update_status(status, *args, **kargs)
