#!/usr/bin/env python
# -*- coding:utf-8 -*-

import tweepy
import tweepywrap
import logging

logger = logging.getLogger("Bot.Steam")

def StreamProcess(queue, consumer_key, consumer_secret, access_key, access_secret):
    """ユーザストリームプロセスの実行内容"""
    logger.info('Standard Input redirects Stream ...')
    while True:
        status = raw_input()
        queue.put((status, ''))


