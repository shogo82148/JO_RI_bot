#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
時刻や日付に関するもろもろ
"""

import re
import datetime
import unicodedata
import random

_re_wakeup = re.compile(ur'[経た]ったら(教えて|起こして)')
_re_weeks = re.compile(ur'(\d+)週間')
_re_days = re.compile(ur'(\d+)日')
_re_hours = re.compile(ur'(\d+)時間')
_re_minutes = re.compile(ur'(\d+)分')
_re_seconds = re.compile(ur'(\d+)秒')

def str2timedelta(text):
    m = _re_weeks.search(text)
    weeks = int(m.group(1)) if m else 0
    m = _re_days.search(text)
    days = int(m.group(1)) if m else 0
    m = _re_hours.search(text)
    hours = int(m.group(1)) if m else 0
    m = _re_minutes.search(text)
    minutes = int(m.group(1)) if m else 0
    m = _re_seconds.search(text)
    seconds = int(m.group(1)) if m else 0

    return datetime.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)

def hook(bot, status):
    text = unicodedata.normalize('NFKC',status.text)
    m = _re_wakeup.search(text)
    if not m:
        return False

    def func(bot):
        bot.reply_to(u'時間だぞー！ [%s]' % bot.get_timestamp(), status)

    dt = str2timedelta(text)
    if dt.days==0 and dt.seconds==0:
        ng_message = random.choice([
                u'いやだ！',
                u'わけがわからないよ',
                u'400 Bad Request'])
        bot.reply_to(ng_message + u" [%s]" % bot.get_timestamp(), status)
    else:
        bot.append_cron(datetime.datetime.now()+dt, func, name = 'wakeup-' + str(status.id))
        
        ok_message = random.choice([
                u'おｋ',
                u'いいよー',
                u'わかったー'])
        bot.reply_to(ok_message + " [%s]" % bot.get_timestamp(), status)
    return True
