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
    content = ''
    with open('', 'r') as conf:
        content = conf.read()
    
    content = content.replace('<YOR_CONSUMER_KEY>', CONSUMER_KEY)
    content = content.replace('<YOR_CONSUMER_SECRET>', CONSUMER_SECRET)
    content = content.replace('<YOR_ACCESS_KEY>', token.key)
    content = content.replace('<YOR_ACCESS_SECRET>', token.secret)
    content = content.replace('<CRAWL_USER>', CRAWL_USER)

    with open('config.py', 'w') as conf:
        conf.write(content)

#設定ファイルの読み込み
try:
    import config
except ImportError:
    #初回実行
    first_run()
    import config

import tweepywrap
import tweepy
from tweepy.error import TweepError
import MeCab
import sqlite3
import time
import signal
import re
import codecs
import sys
import datetime
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
        self._api = tweepy.API(self._auth, retry_count=10, retry_delay=1)

        #アカウント設定の読み込み
        self._name = self._api.me().screen_name
        self._re_reply_to_me = re.compile(r'^@%s' % self._name, re.IGNORECASE)

        #データベースとの接続
        self._db = DBManager(self._mecab)

        #文章生成器の作成
        self._generator = MarkovGenerator(self._db)

        #ユーザリストの作成
        self.ignore_user = [name.lower() for name in config.IGNORE_USER]
        self.admin_user = [name.lower() for name in config.ADMIN_USER]

        #リプライをもらった時のフック
        self.reply_hooks = [
            BotStream.delete_hook,
            BotStream.reply_hook,
            ]

    def start_stream(self):
        """ユーザストリームを開始する"""
        self.log('ユーザストリーム開始')
        stream = tweepy.Stream(self._auth, self)
        try:
            stream.userstream(async=False)
        except tweepy.error.TweepError, e:
            self.log('エラー！', e)

    def start_cron(self):
        """定期実行タスクを開始する"""
        self.log('cronデーモン開始')
        self.crawl()
        cron = crondaemon()
        cron.add('*/20 * * * *', self.post)
        cron.add('30 * * * *', self.crawl)
        cron.add('10 */2 * * *', self.reply_to_bot, args=('@NPoi_bot',))
        cron.add('50 */2 * * *', self.reply_to_bot, args=('@FUCOROID',))
        cron.start(async=False)

    def post(self, text=None):
        """定期ポスト"""
        text = text or self._generator.get_text()
        if len(text)>140:
            text = text[0:140]
        self.log('てーきポスト:', text)
        try:
            self._api.update_status(text)
        except tweepy.error.TweepError, e:
            self.log("エラー！", e)
        return

    def reply_to_bot(self, bot):
        text = bot + ' ' + self._generator.get_text()
        if len(text)>140:
            text = text[0:140]
        self.log('ボットさんへてーきポスト:', text)
        try:
            self._api.update_status(text)
        except tweepy.error.TweepError, e:
            self.log("エラー！", e)
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
            self.log("エラー！", e)

    def delete_hook(self, status):
        """削除命令"""
        if status.text.find(u'削除')<0:
            return False
        if status.author.screen_name.lower() in self.admin_user:
            #削除実行
            if status.in_reply_to_status_id:
                try:
                    res = self._api.destroy_status(status.in_reply_to_status_id)
                    self.log("削除成功:", status.in_reply_to_status_id)
                except:
                    self.log("削除失敗:", status.in_reply_to_status_id)
            else:
                self.reply_to(status, 'in_reply_to入ってないよ！')
            return True
        return False

    def reply_hook(self, status):
        """リプライ返し"""
        self.reply_to(status, self._generator.get_text())
        return True

    def reply_to(self, status, text):
        text = '@%s %s' % (
            status.author.screen_name,
            text)
        if len(text)>140:
            text = text[0:140]
        self.log('リプライ:', text)
        try:
            self._api.update_status(text, in_reply_to_status_id=status.id)
        except tweepy.error.TweepError, e:
            self.log("エラー！", e)

    def log(self, *args):
        self._lock.acquire()
        print datetime.datetime.now(),
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
            #自分へのリプライ

            #ボットさんから話しかけられた場合は無視
            if status.author.screen_name.lower() in self.ignore_user:
                return

            for func in self.reply_hooks:
                ret = func(self, status)
                if ret:
                    break
        else:
            #普通のツイート
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
