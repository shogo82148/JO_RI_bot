#!/usr/bin/env python
# -*- coding:utf-8 -*-

#初回実行時の設定
def first_run():
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

class Bot(tweepywrap.StreamListener):
    def __init__(self):
        self._mecab = MeCab.Tagger()
    
    def start(self):
        #データベースの作成
        auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_KEY, config.ACCESS_SECRET)
        self.api = tweepy.API(auth)

        #定期ポストの設定
        cron = crondaemon()
        cron.add('* * * * *', self.post)
        cron.add('0 * * * *', self.crawl)
        cron.start()

    	#ストリームの開始
        stream = tweepy.Stream(auth, self)
        stream.userstream(async=True)
        while True:
            time.sleep(1000)

    def post(self):
        print '...'
        generator = MarkovGenerator(DBManager())
        status = generator.get_text()
        if len(status)>140:
            status = status[0:140]
        print "Tweet:", status
        self.api.update_status(status)
        return

    def crawl(self):
        print "Crawl!"
        return

    def on_status(self, status):
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

if __name__=="__main__":
    Bot().start()
