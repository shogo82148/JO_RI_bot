# -*- coding: utf-8 -*-
import re
import os

start = re.compile(u'エアコンを?(?:つけ|付け|オン)', re.I)
stop = re.compile(u'エアコンを?(?:とめ|止め|オフ)', re.I)

def match(text):
    for m in _trigger:
        if m.search(text):
            return True
    return False

def hook(bot, status):
    if status.author.screen_name != "shogo82148":
        return False
    if start.search(status.text):
        os.system('~/air-ctrl start')
        bot.reply_to(u'%s [%s]' % (u'エアコンつけたよ', bot.get_timestamp()), status)
        return True

    if stop.search(status.text):
        os.system('~/air-ctrl stop')
        bot.reply_to(u'%s [%s]' % (u'エアコンとめたよ', bot.get_timestamp()), status)
        return True

    return False
