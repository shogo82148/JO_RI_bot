#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
時刻や日付に関するもろもろ
"""

import re
import datetime
import unicodedata
import random
import math

# 漢数字・数字変換
_kanjidigit = u'〇一二三四五六七八九'
_re_kanji = re.compile(u"([" + _kanjidigit + u"])")
_re_kanjijiu1 = re.compile("([" + _kanjidigit + u"])十([" + _kanjidigit + u"])")
_re_kanjijiu2 = re.compile(u"十([" + _kanjidigit + u"])")
_kanjitable = {}
def _initKanji():
    for i, ch in enumerate(_kanjidigit):
        _kanjitable[ch] = str(i)
_initKanji()

def kanji2digit(s):
    """
    1から99までの漢数字をアラビア数字に変換する
    """
    k2d = lambda m, i: _kanjitable[m.group(i)]
    s = _re_kanjijiu1.sub(lambda m: k2d(m,1) + k2d(m,2), s)
    s = _re_kanjijiu2.sub(lambda m: u'1' + k2d(m,1), s)
    s = _re_kanji.sub(lambda m: k2d(m,1), s)
    s = s.replace(u'十', u'10')
    return s

def containsHalf(m):
    return m.group().find(u'半') >= 0

_re_mention = re.compile(u'@\w+')
_re_before_years = re.compile(ur'(\d+)ヵ?年(前|まえ)')
_re_before_months = re.compile(ur'(\d+)ヶ月(前|まえ)')
_re_before_weeks = re.compile(ur'([.\d]+)週間(前|まえ)')
_re_before_days = re.compile(ur'([.\d]+)日半?(前|まえ)')
_re_before_hours = re.compile(ur'([.\d]+)時間半?(前|まえ)')
_re_before_minutes = re.compile(ur'([.\d]+)分半?(前|まえ)')
_re_before_seconds = re.compile(ur'([.\d]+)秒(前|まえ)')
_re_years = re.compile(ur'(\d+)ヵ?年')
_re_months = re.compile(ur'(\d+)ヶ月')
_re_weeks = re.compile(ur'([.\d]+)週間')
_re_days = re.compile(ur'([.\d]+)日半?(後|たった|経った|経過)')
_re_hours = re.compile(ur'([.\d]+)時間半?')
_re_minutes = re.compile(ur'([.\d]+)分半?')
_re_seconds = re.compile(ur'([.\d]+)秒')
_re_tomorrow = re.compile(ur'明日|あす|翌日|よくじつ')
_re_nexttomorrow = re.compile(ur'明後日|あさって|みょうごにち')
_re_nextnexttomorrow = re.compile(ur'明[明々]後日|しあさって')
_re_yesterday = re.compile(ur'昨日|きのう|さくじつ|前日')
_re_daybeforeyesterday = re.compile(ur'1昨日|おと[とつ]い|いっさくじつ')
_am = ur'a\.?m\.?|午前'
_pm = ur'p\.?m\.?|午後'
_re_am = re.compile(_am, re.IGNORECASE)
_re_pm = re.compile(_pm, re.IGNORECASE)
_re_on_time1 = re.compile(ur'(?P<ampm>' + _am + u'|' + _pm + ur')?(?P<hour>\d\d?)時半?((?P<minute>\d\d?)分)?((?P<second>\d\d?)秒)?', re.IGNORECASE)
_re_on_time2 = re.compile(ur'(?P<ampm>' + _am + u'|' + _pm + ur')?(?P<hour>\d\d?):(?P<minute>\d\d?)(:(?P<second>\d\d?))?', re.IGNORECASE)
_re_on_time3 = re.compile(ur'(?P<ampm>' + _am + u'|' + _pm + ur')?(\d\d\d+)', re.IGNORECASE)
_re_day = re.compile(ur'(\d+)日')
_re_monthday1 = re.compile(ur'(?P<month>\d+)月(?P<day>\d+)日')
_re_monthday2 = re.compile(ur'(?P<month>\d+)[-./](?P<day>\d+)')
_re_date1 = re.compile(ur'(?P<name>平成|H)?(?P<year>\d+)年(?P<month>\d+)月(?P<day>\d+)日', re.IGNORECASE)
_re_date2 = re.compile(ur'(?P<name>平成|H)?(?P<year>\d+)[-./](?P<month>\d+)[-./](?P<day>\d+)', re.IGNORECASE)
def gettime(text, now):
    text = unicodedata.normalize('NFKC', text)
    text = kanji2digit(text)
    text = _re_mention.sub('', text)

    pos = 0
    while pos < len(text):
        # 年/月/日
        m = _re_date1.match(text, pos) or _re_date2.match(text, pos)
        if m:
            try:
                year = int(m.group('year'))
                if m.group('name'): # 平成で指定された
                    year += 1988
                month = int(m.group('month'))
                day = int(m.group('day'))
                now = datetime.datetime(year, month, day)
            except:
                pass
            pos += len(m.group())
            continue

        # 秒前
        m = _re_before_seconds.match(text, pos)
        if m:
            now = now - datetime.timedelta(seconds=math.floor(float(m.group(1))))
            pos += len(m.group())
            continue

        # 分前
        m = _re_before_minutes.match(text, pos)
        if m:
            now = now - datetime.timedelta(minutes=float(m.group(1)))
            if containsHalf(m):
                now = now - datetime.timedelta(minutes = 0.5)
            pos += len(m.group())
            continue

        # 時間前
        m = _re_before_hours.match(text, pos)
        if m:
            now = now - datetime.timedelta(hours=float(m.group(1)))
            if containsHalf(m):
                now = now - datetime.timedelta(hours = 0.5)
            pos += len(m.group())
            continue

        # 日前
        m = _re_before_days.match(text, pos)
        if m:
            now = now - datetime.timedelta(days=float(m.group(1)))
            if '.' not in m.group(1):
                now = datetime.datetime(now.year, now.month, now.day)
            if containsHalf(m):
                now = now - datetime.timedelta(days = 0.5)
            pos += len(m.group())
            continue

        # 週前
        m = _re_before_weeks.match(text, pos)
        if m:
            now = now - datetime.timedelta(weeks=float(m.group(1)))
            pos += len(m.group())
            continue

        # 1ヶ月前
        m = _re_before_months.match(text, pos)
        if m:
            # 日にち計算
            month = now.month - int(m.group(1)) - 1
            year = now.year + (month // 12)
            month = month % 12 + 1
            day = now.day

            # その月の最終日を計算
            year2 = year
            month2 = month + 1
            if month2 == 13:
                month2 = 1
                year2 += 1
            now = datetime.datetime(year2, month2, 1) - datetime.timedelta(1)

            # 指定された日が存在すれば置き換え
            if now.day > day:
                now = datetime.datetime(year, month, day)
            pos += len(m.group())
            continue

        # 年前
        m = _re_before_years.match(text, pos)
        if m:
            # 日にち計算
            year = now.year - int(m.group(1))
            month = now.month
            day = now.day

            # その月の最終日を計算
            year2 = year
            month2 = month + 1
            if month2 == 13:
                month2 = 1
                year2 += 1
            now = datetime.datetime(year2, month2, 1) - datetime.timedelta(1)

            # 指定された日が存在すれば置き換え
            if now.day > day:
                now = datetime.datetime(year, month, day)
            pos += len(m.group())
            continue

        # 秒
        m = _re_seconds.match(text, pos)
        if m:
            now = now + datetime.timedelta(seconds=math.floor(float(m.group(1))))
            pos += len(m.group())
            continue

        # 分
        m = _re_minutes.match(text, pos)
        if m:
            now = now + datetime.timedelta(minutes=float(m.group(1)))
            if containsHalf(m):
                now = now + datetime.timedelta(minutes = 0.5)
            pos += len(m.group())
            continue

        # 時間
        m = _re_hours.match(text, pos)
        if m:
            now = now + datetime.timedelta(hours=float(m.group(1)))
            if containsHalf(m):
                now = now + datetime.timedelta(hours = 0.5)
            pos += len(m.group())
            continue

        # 日
        m = _re_days.match(text, pos)
        if m:
            now = now + datetime.timedelta(days=float(m.group(1)))
            if '.' not in m.group(1):
                now = datetime.datetime(now.year, now.month, now.day)
            if containsHalf(m):
                now = now + datetime.timedelta(days = 0.5)
            pos += len(m.group())
            continue

        # 週
        m = _re_weeks.match(text, pos)
        if m:
            now = now + datetime.timedelta(weeks=float(m.group(1)))
            pos += len(m.group())
            continue

        # 1ヶ月
        m = _re_months.match(text, pos)
        if m:
            # 日にち計算
            month = now.month + int(m.group(1)) - 1
            year = now.year + (month // 12)
            month = month % 12 + 1
            day = now.day

            # その月の最終日を計算
            year2 = year
            month2 = month + 1
            if month2 == 13:
                month2 = 1
                year2 += 1
            now = datetime.datetime(year2, month2, 1) - datetime.timedelta(1)

            # 指定された日が存在すれば置き換え
            if now.day > day:
                now = datetime.datetime(year, month, day)
            pos += len(m.group())
            continue

        # 年
        m = _re_years.match(text, pos)
        if m:
            # 日にち計算
            year = now.year + int(m.group(1))
            month = now.month
            day = now.day

            # その月の最終日を計算
            year2 = year
            month2 = month + 1
            if month2 == 13:
                month2 = 1
                year2 += 1
            now = datetime.datetime(year2, month2, 1) - datetime.timedelta(1)

            # 指定された日が存在すれば置き換え
            if now.day > day:
                now = datetime.datetime(year, month, day)
            pos += len(m.group())
            continue

        # 日付指定
        m = _re_day.match(text, pos)
        if m:
            pos += len(m.group())
            year = now.year
            month = now.month
            day = int(m.group(1))
            if day==0 or day>31:
                continue
            try:
                if day < now.day: # 指定された日が過ぎていたら翌月
                    month += 1
                if month == 13:
                    month = 1
                    year = 12
                now = datetime.datetime(year, month, day)
            except:
                pass
            continue

        # 月/日
        m = _re_monthday1.match(text, pos) or _re_monthday2.match(text, pos)
        if m:
            pos += len(m.group())
            year = now.year
            month = int(m.group('month'))
            day = int(m.group('day'))
            try:
                if (month, day) < (now.month, now.day):
                    year += 1
                now = datetime.datetime(year, month, day)
            except:
                pass
            continue

        # 時間指定
        m = _re_on_time1.match(text, pos) or _re_on_time2.match(text, pos)
        if m:
            ampm = m.group('ampm')
            hour = int(m.group('hour') or 0)
            minute = int(m.group('minute') or 0)
            second = int(m.group('second') or 0)
            if ampm and _re_pm.match(ampm):
                hour += 12
            if containsHalf(m):
                minute += 30
            waketime = datetime.datetime(now.year, now.month, now.day)
            waketime = waketime + datetime.timedelta(hours=hour, minutes=minute, seconds=second)
            while waketime <= now:
                if hour <= 12 and not ampm: # 12時間制で「午後」を省略したと仮定
                        waketime += datetime.timedelta(hours = 12)
                else:
                    # 日付を省略したと仮定
                    waketime += datetime.timedelta(1)
            now = waketime
            pos += len(m.group())

        # 明日
        m = _re_tomorrow.match(text, pos)
        if m:
            now = datetime.datetime(now.year, now.month, now.day)
            now = now + datetime.timedelta(1)
            pos += len(m.group())
            continue

        # 明後日
        m = _re_nexttomorrow.match(text, pos)
        if m:
            now = datetime.datetime(now.year, now.month, now.day)
            now = now + datetime.timedelta(2)
            pos += len(m.group())
            continue

        # 明明後日
        m = _re_nextnexttomorrow.match(text, pos)
        if m:
            now = datetime.datetime(now.year, now.month, now.day)
            now = now + datetime.timedelta(3)
            pos += len(m.group())
            continue

        # 昨日
        m = _re_yesterday.match(text, pos)
        if m:
            now = datetime.datetime(now.year, now.month, now.day)
            now = now - datetime.timedelta(1)
            pos += len(m.group())
            continue

        # 一昨日
        m = _re_daybeforeyesterday.match(text, pos)
        if m:
            now = datetime.datetime(now.year, now.month, now.day)
            now = now - datetime.timedelta(2)
            pos += len(m.group())
            continue

        # 数字の羅列を時刻として判定
        m = _re_on_time3.match(text, pos)
        if m:
            hour = 0
            minute = 0
            second = 0
            digits = int(m.group(2))
            if digits >= 10000: # hhmmss形式と仮定
                hour = digits // 10000
                minute = (digits // 100) % 100
                second = digits % 100
            else: # hhmm形式と仮定
                hour = digits // 100
                minute = digits % 100
            ampm = m.group('ampm')
            if ampm and _re_pm.match(ampm):
                hour += 12
            waketime = datetime.datetime(now.year, now.month, now.day)
            waketime = waketime + datetime.timedelta(hours=hour, minutes=minute, seconds=second)
            while waketime <= now:
                if hour <= 12 and not ampm: # 12時間制で「午後」を省略したと仮定
                        waketime += datetime.timedelta(hours = 12)
                else:
                    # 日付を省略したと仮定
                    waketime += datetime.timedelta(1)
            now = waketime
            pos += len(m.group())
            continue

        pos += 1

    return now

_re_dm = re.compile(ur'DM|ダイレクトメッセージ', re.IGNORECASE)
_re_wakeup1 = re.compile(ur'(たら|に)((DM|ダイレクトメッセージ)で?)?(教えて|起こして|教えろ|起こせ)', re.IGNORECASE)
_re_wakeup2 = re.compile(ur'(たら|に)(DM|ダイレクトメッセージ)を?(送って|送れ)', re.IGNORECASE)
_re_cancel = re.compile(ur'キャンセル|いいや')
_re_3minutes = re.compile(ur'お?[湯ゆ][入い]れた')
_re_40seconds = re.compile(ur'連れて[い行]?って')
def hook(bot, status):
    def makewakehook(message = u'時間だぞー！'):
        def wake(bot):
            text = u'%s [%s]' % (message, bot.get_timestamp())
            if is_dm:
                bot.api.send_direct_message(user=status.author.id, text=text)
            else:
                if target_users:
                    text = ' '.join(target_users) + ' ' + text
                bot.reply_to(text , status)
        return wake

    def cancel_hook(bot, new_status):
        m = _re_cancel.search(new_status.text)
        if not m:
            return False
        if new_status.author.id == status.author.id:
            bot.reply_to(u'はーい、またいつでもどうぞー [%s]' % bot.get_timestamp(), new_status)
            bot.delete_reply_hook(name)
            return True
        author_name = u'@' + new_status.author.screen_name.lower()
        if author_name in target_users_set:
            bot.reply_to(u'はーい、またいつでもどうぞー [%s]' % bot.get_timestamp(), new_status)
            target_users_set.remove(author_name)
            target_users[:] = [n for n in target_users if name.lower() != author_name]
            return True

    def makeokreply(ok_message, time_out, wakehook = None):
        if target_users:
            ok_message = ' '.join(target_users) + ' ' + ok_message
        ok_status = bot.reply_to(ok_message + " [%s]" % bot.get_timestamp(), status)
        bot.append_reply_hook(cancel_hook,
                              name = name,
                              in_reply_to = ok_status.id,
                              time_out = time_out,
                              on_time_out = wakehook or makewakehook())

    text = unicodedata.normalize('NFKC',status.text)
    is_dm = not (_re_dm.search(text) is None)
    name = 'wakeup-' + str(status.id)

    # 他の人にもお知らせする
    myscreenname = u'@' + bot.api.me().screen_name.lower()
    target_users = []
    target_users_set = set([u'@' + status.author.screen_name.lower()])
    for m in _re_mention.finditer(status.text):
        if m.group().lower() == myscreenname:
            continue
        if m.group().lower() in target_users_set:
            continue
        target_users.append(m.group())
        target_users_set.add(m.group().lower())
    target_users = target_users[:4] # 最大3人まで
    target_users_set = set(target_users)

    if _re_3minutes.search(text):
        makeokreply(u'3分間待ってやる', 3*60, makewakehook(u'時間だ！！答えを聞こう！！'))
        return True
    elif _re_40seconds.search(text):
        makeokreply(u'40秒で支度しな', 3*60, makewakehook(u'時間だ！！'))
        return True

    m = _re_wakeup1.search(text) or _re_wakeup2.search(text)
    if not m:
        return False

    try:
        waketime = gettime(text, datetime.datetime.now())
    except Exception:
        waketime = None

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
        makeokreply(ok_message, waketime-datetime.datetime.now())
    return True
