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
from crondaemon import crondaemon
from dbmanager import DBManager
from generator import MarkovGenerator
from multiprocessing import Process

class BotStream(tweepywrap.StreamListener):
    def __init__(self):
        super(BotStream, self).__init__()

        self._mecab = MeCab.Tagger()

        #APIの作成
        self._auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        self._auth.set_access_token(config.ACCESS_KEY, config.ACCESS_SECRET)
        self._api = tweepy.API(self._auth)

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
        cron.add('* * * * *', self.post)
        cron.start(async=False)

    def post(self):
        self._api.update_status(self._generator.get_text())
        return

    def on_status(self, status):
        print status.text
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

def StreamingProcess():
    BotStream().start_stream()

def CronDaemon():
    BotStream().start_cron()

if __name__=="__main__":
    streaming_process = Process(target=StreamingProcess)
    streaming_process.start()
    cron_process = Process(target=CronDaemon)
    cron_process.start()
