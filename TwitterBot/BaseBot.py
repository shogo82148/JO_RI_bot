#!/usr/bin/env python
# -*- coding:utf-8 -*-

import tweepy
import tweepy.binder
import tweepywrap
import time
import httplib
import re
import codecs
import sys
import datetime
import crondaemon
import logging
import logging.handlers
from multiprocessing import Process, Lock, Queue
import traceback
from TwitterStream import StreamProcess

logger = logging.getLogger("Bot")

PRIORITY_ADMIN = 0
PRIORITY_IN_REPLY_TO = 1
PRIORITY_NORMAL = 2

class BotShutdown(Exception):
    """ボットをシャットダウンしたいときに投げる例外"""
    pass

class APIMock(object):
    def __to_string(self, obj):
        if isinstance(obj, str):
            return "'%s'" % obj
        elif isinstance(obj, unicode):
            return "u'%s'" % obj.encode('utf-8')
        else:
            return str(obj)
    def __getattr__(self, name):
        myname = name
        def func(*args, **kargs):
            print myname + ':'
            for arg in args:
                print '\t' + self.__to_string(arg)
            for name, arg in kargs.iteritems():
                print '\t%s=%s' % (name, self.__to_string(arg))
            print
        return func

    def update_status(self, status, in_reply_to_status_id=None, lat=None, long=None, source=None, place_id=None):
        class Mock(object):
            pass
        print 'update_status:'
        print '\tstatus=%s' % self.__to_string(status)
        if in_reply_to_status_id:
            print '\tin_reply_to_status_id=%s' % self.__to_string(in_reply_to_status_id)
        if lat:
            print '\tlat=%s' % self.__to_string(lat)
        if long:
            print '\tlong=%s' % self.__to_string(long)
        if source:
            print '\tlat=%s' % self.__to_string(source)
        if place_id:
            print '\tlat=%s' % self.__to_string(place_id)
        s = Mock()
        s.id = 2345678900
        s.text = status
        s.in_reply_to_status_id = in_reply_to_status_id
        s.created_at = datetime.datetime.now()
        s.author = Mock()
        s.author.screen_name = u'test_user'
        s.author.name = u'テスト垢'
        s.author.id = 123
        return s

    def rate_limit_status(self):
        return {"reset_time_in_seconds": 1277485629,
                "remaining_hits": 350,
                "hourly_limit": 350,
                "reset_time": "Fri Jun 25 17:07:09 +0000 2010"}

class BaseBot(tweepywrap.StreamListener):
    def __init__(self, consumer_key, consumer_secret, access_key, access_secret):
        #API設定
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_key = access_key
        self._access_secret = access_secret

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
        parser.add_option('-i', '--interactive',
                          dest='interactive',
                          default=False,
                          action='store_true',
                          help="Interactive Test",
                          )
        parser.add_option('-c', '--cron',
                          dest='cron',
                          default='',
                          help="Test cron tasks",
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
        if options.interactive:
            self.start_interactive()
        elif options.cron:
            self.test_cron(options.cron)
        else:
            self.start()

    def start(self):
        """ボットの動作を開始する"""

        # API初期化
        auth = tweepy.OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_key, self._access_secret)
        api = tweepy.API(auth, retry_count=10, retry_delay=1)
        self.api = api
        self.configure = {}
        self.tweet_length = 140

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

        #ユーザストリームを別プロセスで開始
        args = (self._queue, self._consumer_key, self._consumer_secret, self._access_key, self._access_secret)
        streaming_process = Process(target=StreamProcess, args = args)
        streaming_process.daemon = True
        streaming_process.start()

        #cronサービスを開始
        logger.info(u'Cron Daemon Starting...')
        self._cron.start(async=True)

        # メインループ
        self.on_start()
        while streaming_process.is_alive():
            try:
                data_type, data = self._queue.get()
                if data_type=='stream':
                    self.on_data(data)
                elif data_type=='cron':
                    self._cron_funcs[data]()
                elif data_type=='shutdown':
                    logger.warning('Shutdown Message Received')
                    break
            except BotShutdown, e:
                logger.warning('Shutdown Message Received')
                break
            except KeyboardInterrupt, e:
                logger.warning('Keyboard Interrupt')
                break
            except Exception, e:
                logger.error(str(e).decode('utf-8'))
                logger.error(traceback.format_exc())

        try:
            self.on_shutdown()
        except Exception, e:
            logger.error(str(e).decode('utf-8'))

        self._cron.stop()
        logger.info(u'Shutdown')

    def start_interactive(self):
        """コンソール経由でボットとはなす"""

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
        user = MockTweepy.getUser('test')

        # メインループ
        self.on_start()
        latest_id = None
        while True:
            try:
                print '>>',
                sys.stdout.flush()
                text = raw_input().decode('utf-8')
                a = text.split()
                if len(a)==0:
                    pass
                elif a[0] == 'shutdown':
                    raise BotShutdown()
                else:
                    text = u'@' + self._name + u' ' + text
                    status = api.getStatus(text=text, user=user, in_reply_to_status_id=latest_id)
                    self.on_data(json.dumps(status))
                    latest_id = api.getLatestId()
                    print latest_id

            except BotShutdown, e:
                logger.warning('Shutdown Message Received')
                break
            except KeyboardInterrupt, e:
                logger.warning('Keyboard Interrupt')
                break
            except EOFError, e:
                break
            except Exception, e:
                logger.error(str(e).decode('utf-8'))
                logger.error(traceback.format_exc())

        try:
            self.on_shutdown()
        except Exception, e:
            logger.error(str(e).decode('utf-8'))

        logger.info(u'Shutdown')

    def test_cron(self, cron_id):
        self.api = APIMock()
        func = self._cron_funcs.get(cron_id)
        if func:
            func()
        else:
            print u'Cron task not found'
            print u'Cron tasks:'
            for key in self._cron_funcs.iterkeys():
                print "\t" + key

    def on_start(self):
        pass

    def on_shutdown(self):
        pass

    def append_reply_hook(self, func, priority=None, name=None, in_reply_to=None, time_out=None, on_time_out=None):
        """リプライフックを追加する"""
        reply_hook_id = name or (u'reply-hook-' + str(self._reply_hook_id))
        self._reply_hook_id += 1

        def cron_time_out(bot):
            bot.delete_reply_hook(reply_hook_id)
            if on_time_out:
                on_time_out(bot)
        if time_out:
            if priority is None:
                priority = PRIORITY_IN_REPLY_TO
            if isinstance(time_out, datetime.timedelta):
                dt = time_out
            else:
                dt = datetime.timedelta(seconds=time_out)
            self.append_cron(datetime.datetime.now()+dt, cron_time_out, name=u'timeout-'+reply_hook_id)
        if priority is None:
            priority = PRIORITY_NORMAL
        self._reply_hooks.append([priority, reply_hook_id, func, in_reply_to])
        self._reply_hooks.sort(key=lambda x: x[0])
        return reply_hook_id

    def delete_reply_hook(self, name):
        self.delete_cron(u'timeout-'+name)
        self._reply_hooks = [h for h in self._reply_hooks if h[1]!=name]
        return name

    def append_cron(self, crontime, func, args=(), kargs={}, name=None):
        """定期実行タスクを追加する"""
        cron_id = name or (u'cron-' + str(self._cron_id))
        self._cron_id += 1

        def wrap():
            logger.info(u'Running ' + cron_id)
            func(self, *args, **kargs)
            if not self._cron.hascron(cron_id):
                self.delete_cron(cron_id)

        def put():
            self._queue.put(('cron', cron_id))

        self._cron_funcs[cron_id] = wrap
        self._cron.append(crontime, put, name=cron_id)
        return cron_id

    def delete_cron(self, name):
        self._cron.delete(name)
        if name in self._cron_funcs:
            del self._cron_funcs[name]
        else:
            return None
        return name

    def on_status(self, status):
        """ステータス取得"""
        if self._re_reply_to_me.search(status.text):
            logger.info('recieved:' + status.text)
            for priority, name, func, in_reply_to in self._reply_hooks:
                if in_reply_to and in_reply_to!=status.in_reply_to_status_id:
                    continue
                ret = func(self, status)
                if ret:
                    break

    def get_timestamp(self):
        return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

    def update_status(self, status, *args, **kargs):
        logger.info(u'update: ' + status)
        return self.api.update_status(status, *args, **kargs)

    def destroy_status(self, status_id):
        logger.info(u'delete: %d' % int(status_id))
        return self.api.destroy_status(status_id)

    def reply_to(self, status, in_reply_to, cut=True):
        text = u'@%s %s' % (in_reply_to.author.screen_name, status)
        if cut and len(text)>140:
            text = text[0:140]
        return self.update_status(text,
                           in_reply_to_status_id=in_reply_to.id)

    def update_configure(self):
        bind_api = tweepy.binder.bind_api
        get_configure = bind_api(
            path = '/help/configuration.json',
            payload_type = 'json')
        self.configure = get_configure(self.api)
        print self.configure

