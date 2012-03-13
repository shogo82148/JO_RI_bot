#!/usr/bin/env python
# -*- coding:utf-8 -*-

import config
import BaseBot

def reply(bot, status):
    bot.reply_to(u'リプライありがとう！ [%s]' % bot.get_timestamp(), status)

def tweet(bot):
    bot.update_status(u'よるほー')

def main():
    bot = BaseBot.BaseBot(config.CONSUMER_KEY,
                        config.CONSUMER_SECRET,
                        config.ACCESS_KEY,
                        config.ACCESS_SECRET)
    bot.append_cron('00 00 * * *', tweet)
    bot.append_reply_hook(reply)
    bot.main()
    
if __name__=='__main__':
    main()
