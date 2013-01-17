# -*- coding: utf-8 -*-

"""
ツイッターにいるキモ童貞の真似しまーーーーーすwwwwww
大丈夫か(´・ω・)
俺でよければ話聞くぞ？(´・ω・`)
無理するなよ(´・ω・)
話して楽になったなら良かった(´・ω・`)
https://twitter.com/hidacaw/status/288661466456915968
"""

import re
import random

_trigger = [
    re.compile(u'(?:じょり|ジョリ|JO_RI)(?!ぼ|ボ|_bot)', re.I),
    re.compile(ur'[/:;・]_;'),
    re.compile(ur'T[_oOдД]T'),
    re.compile(ur';O;'),
    re.compile(ur'>_<'),
    re.compile(ur'´・ω・[`｀]'),
    re.compile(ur'´；ω；｀'),
    re.compile(ur'｀；ω；´'),
    ]

def match(text):
    for m in _trigger:
        if m.search(text):
            return True
    return False

def hook(bot, status):
    def reply_hook(bot, status):
        res = random.choice([u'大丈夫か＾＾', u'俺でよければ話し聞くぞ＾＾', u'無理するなよ＾＾', u'話して楽になったなら良かった＾＾'])
        new_status = bot.reply_to(u'%s [%s]' % (res, bot.get_timestamp()), status)
        if res[0] != u'話':
            bot.append_reply_hook(reply_hook, name='tellme-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)
        return True

    if not match(status.text):
        return False

    res = random.choice([u'大丈夫か＾＾', u'俺でよければ話し聞くぞ＾＾', u'無理するなよ＾＾'])
    new_status = bot.reply_to(u'%s [%s]' % (res, bot.get_timestamp()), status)
    bot.append_reply_hook(reply_hook, name='tellme-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)
    return True
