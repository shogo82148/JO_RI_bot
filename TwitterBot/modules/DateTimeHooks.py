#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
時刻や日付に関するもろもろ
"""

import re
import datetime
import unicodedata
import random

_re_dm = re.compile(ur'DM|ダイレクトメッセージ', re.IGNORECASE)
_re_wakeup1 = re.compile(ur'たら((DM|ダイレクトメッセージ)で?)?(教えて|起こして)', re.IGNORECASE)
_re_wakeup2 = re.compile(ur'たら(DM|ダイレクトメッセージ)を?送って', re.IGNORECASE)
_re_cancel = re.compile(ur'キャンセル|いいや')
_re_weeks = re.compile(ur'(\d+)週間')
_re_days = re.compile(ur'(\d+)日')
_re_hours = re.compile(ur'(\d+)時間')
_re_minutes = re.compile(ur'(\d+)分')
_re_seconds = re.compile(ur'(\d+)秒')
_re_milliseconds = re.compile(ur'(\d+)ミリ秒')
_re_on_time1 = re.compile(ur'(?P<hour>\d\d?)時((?P<minute>\d\d?)分)?((?P<second>\d\d?)秒)?に')
_re_on_time2 = re.compile(ur'(?P<hour>\d\d?):(?P<minute>\d\d?)(:(?P<second>\d\d?))?に')
_re_on_time3 = re.compile(ur'(\d+)に')
_re_3minutes = re.compile(ur'湯入')
_re_40seconds = re.compile(ur'連れてい?って')
def gettime(text):
    now = datetime.datetime.now()
    m = _re_on_time1.search(text) or _re_on_time2.search(text)
    if m:
        hour = int(m.group('hour') or 0)
        minute = int(m.group('minute') or 0)
        second = int(m.group('second') or 0)
        if minute>=60 or second>=60:
            return None
        waketime = datetime.datetime(now.year, now.month, now.day) + \
            datetime.timedelta(hours=hour, minutes=minute, seconds=second)
        if hour<=12 and waketime<now:
            #12時間制で指定しているものとする
            waketime += datetime.timedelta(hours=12)
        return waketime

    m = _re_on_time3.search(text)
    if m and len(m.group(1))>=3:
        minute = int(m.group(1)) % 100
        hour = int(m.group(1)) / 100
        if minute>=60:
            return None
        waketime = datetime.datetime(now.year, now.month, now.day) + \
            datetime.timedelta(hours=hour, minutes=minute)
        if hour<=12 and waketime<now:
            #12時間制で指定しているものとする
            waketime += datetime.timedelta(hours=12)
        return waketime

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
    m = _re_milliseconds.search(text)
    milliseconds = int(m.group(1)) if m else 0
    if weeks or days or hours or minutes or seconds or milliseconds:
        return now + datetime.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds)

def hook(bot, status):
    def makewakehook(message = u'時間だぞー！'):
        def wake(bot):
            text = u'%s [%s]' % (message, bot.get_timestamp())
            if is_dm:
                bot.api.send_direct_message(user=status.author.id, text=text)
            else:
                bot.reply_to(text , status)
        return wake

    def cancel_hook(bot, new_status):
        m = _re_cancel.search(new_status.text)
        if not m:
            return False
        if new_status.author.id!=status.author.id:
            return False
        bot.reply_to(u'はーい、またいつでもどうぞー [%s]' % bot.get_timestamp(), new_status)
        bot.delete_reply_hook(name)
        return True

    text = unicodedata.normalize('NFKC',status.text)
    is_dm = not (_re_dm.search(text) is None)
    name = 'wakeup-' + str(status.id)
    if _re_3minutes.search(text):
        ok_status = bot.reply_to(u'3分間待ってやる [%s]' % bot.get_timestamp(), status)
        bot.append_reply_hook(cancel_hook,
                              name = name,
                              in_reply_to = ok_status.id,
                              time_out = 3*60,
                              on_time_out = makewakehook(u'時間だ！！答えを聞こう！！'))
        return True
    elif _re_40seconds.search(text):
        ok_status = bot.reply_to(u'40秒で支度しな [%s]' % bot.get_timestamp(), status)
        bot.append_reply_hook(cancel_hook,
                              name = name,
                              in_reply_to = ok_status.id,
                              time_out = 40,
                              on_time_out = makewakehook(u'時間だ！！'))
        return True

    m = _re_wakeup1.search(text) or _re_wakeup2.search(text)
    if not m:
        return False
    waketime = gettime(text)

    if waketime is None or waketime-datetime.datetime.now()<datetime.timedelta(seconds=9):
        ng_message = random.choice([
                u'いやだ！',
                u'だが断る',
                u'わけがわからないよ',
                u'400 Bad Request'])
        bot.reply_to(ng_message + u" [%s]" % bot.get_timestamp(), status)
    else:
        ok_message = random.choice([
                u'おｋ ',
                u'いいよー ',
                u'はーい ',
                u'わかったー '])
        ok_message += waketime.strftime('%Y/%m/%d %H:%M:%S')
        if is_dm:
            ok_message += u'にDMでお知らせします'
        else:
            ok_message += u'にお知らせします'
        ok_status = bot.reply_to(ok_message + " [%s]" % bot.get_timestamp(), status)

        bot.append_reply_hook(cancel_hook,
                              name = name,
                              in_reply_to = ok_status.id,
                              time_out = waketime-datetime.datetime.now(),
                              on_time_out = makewakehook())
    return True
