#!/usr/bin/env python
# -*- coding:utf-8 -*-

import bot
import tweepy
import config
import codecs
import sys
import os
import re

sys.stdin = codecs.getreader('utf-8')(sys.stdin)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

def main():
    auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
    auth.set_access_token(config.ACCESS_KEY, config.ACCESS_SECRET)
    api = tweepy.API(auth, retry_count=10, retry_delay=1)

    arg = {}
    arg["status"] = " ".join(sys.argv[1:])

    if(re.match(r"[0-9.\-]+,[0-9.\-]+", sys.argv[-1])):
        arg["lat"], arg["long"] = sys.argv[-1].split(',')
        arg["status"] = " ".join(sys.argv[1:-1])
    arg["status"] = "【お知らせ】" + arg["status"]

    api.update_status(**arg)

if __name__ == "__main__":
  main()
