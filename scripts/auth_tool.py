#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import tweepy

if __name__ == "__main__":
  consumer_key = raw_input('Your Consumer Key:')
  consumer_secret = raw_input('Your Consumer Secret')
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

  # ユーザにアプリケーションの許可を求めるためのURLを表示
  print 'Please access this URL: ' + auth.get_authorization_url()

  # PINを入力してもらう
  pin = raw_input('Please input verification PIN from twitter.com: ').strip()

  # Access Tokenの取得と表示
  token = auth.get_access_token(verifier=pin)
  print 'Access token:'
  print '  Key: %s' % token.key
  print '  Secret: %s' % token.secret

