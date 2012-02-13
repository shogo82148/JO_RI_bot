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
_re_cancel = re.compile(ur'キャンセル|いいや')
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
    name = 'wakeup-' + str(status.id)

    def wake(bot):
        bot.reply_to(u'時間だぞー！ [%s]' % bot.get_timestamp(), status)

    def cancel_hook(bot, new_status):
        m = _re_cancel.search(new_status.text)
        if not m:
            return False
        if new_status.author.id!=status.author.id:
            return False
        bot.reply_to(u'はーい、またいつでもどうぞー [%s]' % bot.get_timestamp(), new_status)
        bot.delete_reply_hook(name)
        return True

    dt = str2timedelta(text)
    if dt.days==0 and dt.seconds==0:
        ng_message = random.choice([
                u'いやだ！',
                u'わけがわからないよ',
                u'400 Bad Request'])
        bot.reply_to(ng_message + u" [%s]" % bot.get_timestamp(), status)
    else:        
        ok_message = random.choice([
                u'おｋ',
                u'いいよー',
                u'わかったー'])
        ok_status = bot.reply_to(ok_message + " [%s]" % bot.get_timestamp(), status)

        bot.append_reply_hook(cancel_hook,
                              name = name,
                              in_reply_to = ok_status.id,
                              time_out = dt,
                              on_time_out = wake)
    return True
