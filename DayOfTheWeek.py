#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
曜日計算機能
"""

import re
import datetime
import unicodedata
from jholiday import holiday_name

_re_date = re.compile(ur'(西暦|平成|昭和|大正|明治)?(元|\d+)[/年](\d+)[/月](\d+)日?は何曜日')
_week_name = [u'月', u'火', u'水', u'木', u'金', u'土', u'日']
def hook(bot, status):
    m = _re_date.search(unicodedata.normalize('NFKC',status.text))
    if not m:
        return False

    nengo = m.group(1)
    if m.group(2)==u'元':
        year = 1
    else:
        year = int(m.group(2))
    month = int(m.group(3))
    day = int(m.group(4))

    try:
        if year==0:
            raise Exception()
        if nengo==u'平成':
            #1989年1月8日から
            year += 1988
            if year==1989 and month==1 and day<8:
                raise Exception()
        elif nengo==u'昭和':
            #1926年12月25日から1989年1月7日まで
            year += 1925
            if year==1926 and (month<12 or day<25):
                raise Exception()
            if year==1989 and (month>1 or day>7):
                raise Exception()
        elif nengo==u'大正':
            #1912年7月30日から1926年12月25日まで
            year += 1911
            if year==1912 and (month<7 or (month==7 and day<30)):
                raise Exception()
            if year==1926 and month==12 and day>25:
                raise Exception()
        elif nengo==u'明治':
            #1868年1月25日から1912年7月30日まで
            year += 1867
            if year==1868 and month==1 and day<25:
                raise Exception()
            if year==1912 and (month>7 or (month==7 and day>30)):
                raise Exception()
        date = datetime.date(year, month, day)
        hname = holiday_name(year, month, day)
        weekday = date.weekday()
        
        if hname:
            text = u'%d年%d月%d日は%s曜日、%sです。' % (year, month, day, _week_name[weekday], hname)
        else:
            text = u'%d年%d月%d日は%s曜日です。' % (year, month, day, _week_name[weekday])
    except Exception, e:
        print e
        text = u'そんな日付は存在しません。'
    
    text += ' [%s]' % bot.get_timestamp()
    bot.reply_to(text, status)
    return True
