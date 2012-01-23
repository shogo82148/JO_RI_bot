#!/usr/bin/env python
# -*- coding:utf-8 -*-

#初回実行時の設定
def first_run():
    import tweepy

    #Twitter 認証
    CONSUMER_KEY = raw_input('Consumer Key?:')
    CONSUMER_SECRET = raw_input('Consumer Secret?:')
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

    print 'Please acess this URL:', auth.get_authorization_url()
    pin = raw_input('Your PIN?:')
    
    token = auth.get_access_token(verifier=pin)
    print 'Your Access token is:'
    print '  Key: %s' % token.key
    print '  Secret: %s' % token.secret

    #クロール設定
    CRAWL_USER = raw_input('Crawling User?:')
    
    #configファイルの作成
    with open('config.py', 'w') as conf:
        conf.write('#!/usr/bin/env python\n')
        conf.write('# -*- coding:utf-8 -*-\n')
        conf.write('CONSUMER_KEY = "%s"\n' % CONSUMER_KEY)
        conf.write('CONSUMER_SECRET = "%s"\n' % CONSUMER_SECRET)
        conf.write('ACCESS_KEY = "%s"\n' % token.key)
        conf.write('ACCESS_SECRET = "%s"\n' % token.secret)
        conf.write('\n')
        conf.write('CRAWL_USER = "%s"\n' % CRAWL_USER)

#設定ファイルの読み込み
try:
    import config
except ImportError:
    #初回実行
    first_run()
    import config

import tweepywrap
import tweepy
import MeCab
import sqlite3
import time
import signal
import re
import codecs
import sys
from crondaemon import crondaemon
from dbmanager import DBManager
from generator import MarkovGenerator
from multiprocessing import Process, Lock

class BotStream(tweepywrap.StreamListener):
    def __init__(self, lock):
        super(BotStream, self).__init__()

        self._lock = lock
        self._mecab = MeCab.Tagger()

        #APIの作成
        self._auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        self._auth.set_access_token(config.ACCESS_KEY, config.ACCESS_SECRET)
        self._api = tweepy.API(self._auth)

        #アカウント設定の読み込み
        self._name = self._api.me().screen_name
        self._re_reply_to_me = re.compile(r'^@%s' % self._name, re.IGNORECASE)

        #データベースとの接続
        self._db = DBManager(self._mecab)

        #文章生成器の作成
        self._generator = MarkovGenerator(self._db)

    def start_stream(self):
        """ユーザストリームを開始する"""
        stream = tweepy.Stream(self._auth, self)
        stream.userstream(async=False)

    def start_cron(self):
        """定期実行タスクを開始する"""
        cron = crondaemon()
        cron.add('*/20 * * * *', self.post)
        cron.add('30 * * * *', self.crawl)
        cron.start(async=False)

    def post(self):
        """定期ポスト"""
        text = self._generator.get_text()
        self.log('てーきポスト:', text)
        self._api.update_status(text)
        return

    def crawl(self):
        """オリジナルユーザの発言をクロール"""
        db = self._db
        api = self._api
        arg = {}
        arg['id'] = config.CRAWL_USER
        self.log('クロールなう')
        if self._db.since_id:
            arg['since_id'] = db.since_id
        try:
            statuses = tweepy.Cursor(api.user_timeline, **arg).items(3200)
            for status in statuses:
                text = db.extract_text(status.text)
                self.log('クロール:', text, status.id)
                db.add_text(text)
                db.since_id = status.id
        except tweepy.error.TweepError, e:
            print e

    def reply_to(self, status, text):
        text = '@%s %s' % (
            status.author.screen_name,
            text)
        if len(text)>140:
            text = text[0:140]
        self.log('リプライ:', text)
        self._api.update_status(text, in_reply_to_status_id=status.id)

    def log(self, *args):
        self._lock.acquire()
        for msg in args:
            if isinstance(msg, str):
                print msg.decode('utf-8'),
            elif isinstance(msg, unicode):
                print msg,
            else:
                print str(msg).decode('utf-8'),
        print
        sys.stdout.flush()
        self._lock.release()

    def on_status(self, status):
        if self._re_reply_to_me.search(status.text):
            #Reply to me
            if status.author.screen_name=='NPoi_bot':
                return
            self.reply_to(status, self._generator.get_text())
        else:
            #Normal Tweets
            pass
        return

    def on_delete(self, status_id, user_id):
        return

    def on_limit(self, track):
        return
    
    def on_follow(self, target, source):
        return

    def on_favorite(self, target, source):
        return

    def on_unfavorite(self, target, source):
        return
    
    def on_error(self, status_code):
        return
        
    def on_timeout(self):
        return

def StreamingProcess(lock):
    BotStream(lock).start_stream()

def CronDaemon(lock):
    BotStream(lock).start_cron()


sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

if __name__=="__main__":
    lock = Lock()
    streaming_process = Process(target=StreamingProcess, args=(lock,))
    streaming_process.start()
    cron_process = Process(target=CronDaemon, args=(lock,))
    cron_process.start()
