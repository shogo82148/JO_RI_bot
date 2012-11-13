#!/usr/bin/env python
# -*- coding:utf-8 -*-

import tweepy
import tweepywrap
import logging
import httplib
import time

logger = logging.getLogger("Bot.Steam")

def StreamProcess(queue, consumer_key, consumer_secret, access_key, access_secret):
    """ユーザストリームプロセスの実行内容"""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    stream = tweepy.Stream(auth, BotStream(queue))
    logger.info('User Stream Starting...')
    while True:
        try:
            stream.userstream(async=False)
        except Exception, e:
            logger.error(str(e).encode('utf-8'))
            time.sleep(10)
            logger.info('Retry to start user stream...')

class BotStream(tweepywrap.StreamListener):
    """ユーザーストリームのリスナ"""
    def __init__(self, queue):
        super(BotStream, self).__init__()
        self.queue = queue

    def on_data(self, data):
        """メインプロセスへ通知"""
        self.queue.put(('stream', data))
