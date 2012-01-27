#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
長岡駅-技大間のバスの発車時刻ツイート
"""
import datetime
import re
import sys
from jholiday import holiday_name

#長岡駅発のバス時刻表
# 駅発車時刻, 技大着, 休日運休Flag(Default:False), 技大入り口に止まらない(Default:False)
station_time_table = (
    (( 7,10), ( 7,40), True),
    (( 7,45), ( 8,13)),
    (( 8, 0), ( 8,30), True),
    (( 8,10), ( 8,38)),
    (( 8,30), ( 8,58)),
    (( 9, 5), ( 9,35)),
    (( 9,35), None),
    ((10, 5), (10,35)),
    ((10,35), (11, 3)),
    ((11, 5), (11,35)),
    ((11,35), (12, 3)),
    ((12, 5), (12,35)),
    ((12,35), None),
    ((13, 5), (13,35)),
    ((13,35), (14, 3)),
    ((14, 5), (14,35)),
    ((14,35), (15, 3)),
    ((15, 5), (15,35)),
    ((15,35), None),
    ((16, 5), (16, 33)),
    ((16,35), None),
    ((17, 5), (17,33)),
    ((17,35), (18, 3)),
    ((18,10), None, True, True),
    ((18,35), (19, 3)),
    ((19, 5), (19,33)),
    ((19,30), None, True),
    ((20,30), None, False, True),
    ((21,20), None, False, True),
)

#技大発のバス時刻表
# 技大発車時刻, 長岡駅着, 休日運休Flag
nut_time_table = (
    (( 7,55),( 8,23), True),
    (( 9, 5),( 9,33)),
    (( 9,55),(10,25)),
    ((10,55),(11,25)),
    ((11,25),(11,53)),
    ((11,55),(12,25)),
    ((12,25),(12,53)),
    ((12,55),(13,25)),
    ((13,55),(14,25)),
    ((14,25),(14,53)),
    ((14,55),(15,25)),
    ((15,25),(15,53)),
    ((15,55),(16,25)),
    ((16,55),(17,25)),
    ((17,55),(18,23), True),
    ((18,15),(18,43)),
    ((19,10),(19,40)),
    ((19,40),(20, 8)),
)

def _to_datetime(date, time_tuple):
    """(hour, minute)のタプルをdatetimeに変換"""
    if time_tuple:
        return datetime.datetime.combine(
            date, datetime.time(time_tuple[0], time_tuple[1]))
    else:
        return None

def _is_holiday(date):
    """休日か否かを返す"""
    weekday = date.weekday()
    if weekday==5 or weekday==6:
        return True
    if date.month==8 and 14<=date.day and date.day<=16:
        return True
    if date.month==12 and date.day>=29:
        return True
    if date.month==1 and date.day<=3:
        return True
    return holiday_name(date=date)

def BusIterator(time_table, start=None):
    """バス発車時刻を返すイテレータ"""

    #当日分の時刻を返す
    start = start or datetime.datetime.now()
    today = start.date()
    start_time = (start.hour, start.minute)
    is_holiday = _is_holiday(today)
    for item in time_table:
        #すでに発車したバスをスキップ
        if item[0]<=start_time:
            continue
        #休日発車運休のバスをスキップ
        if is_holiday and len(item)>=3 and item[2]:
            continue
        info = None
        if len(item)>=4:
            info = item[3]
        yield _to_datetime(today, item[0]), _to_datetime(today, item[1]), info

    #翌日以降の時刻
    while True:
        today += datetime.timedelta(1)
        is_holiday = _is_holiday(today)
        for item in time_table:
            #休日発車運休のバスをスキップ
            if is_holiday and len(item)>=3 and item[2]:
                continue
            info = None
            if len(item)>=4:
                info = item[3]
            yield _to_datetime(today, item[0]), _to_datetime(today, item[1]), info

class Bus(object):
    _re_to_station = re.compile(ur'駅(着|行|ゆき|いき|まで)')
    _re_to_nut = re.compile(ur'(技大|大学)(着|行|ゆき|いき|まで)')

    def hook(self, bot, status):
        text = self.get_message(status.text)
        if text is False:
            return False
        bot.reply_to(text + '[%s]' % bot.get_timestamp(), status)
        return True

    def get_message(self, text, now = None):
        if text.find(u'バス')<0 or text.find(u'時')<0:
            return False

        from_stop = 'nut'
        if self._re_to_station.search(text):
            from_stop = 'nut'
        elif text.find(u'駅')>=0:
            from_stop = 'station'
        elif self._re_to_nut.search(text):
            from_stop = 'station'
        elif text.find(u'技大')>=0 or text.find(u'大学')>=0:
            from_stop = 'nut'
        
        now = now or datetime.datetime.now()
        today = now.date()
        if from_stop=='nut':
            busiter = BusIterator(nut_time_table, now)
            next_start = next(busiter)
            next_next_start = next(busiter)
            if next_start[0].date()!=today:
                text = u'技大発の最終バスは行ってしまいました。次のバスは明日の%d:%02d技大発、%d:%02d長岡駅着だよ。' % (
                    next_start[0].hour, next_start[0].minute, next_start[1].hour, next_start[1].minute)
            elif next_next_start[0].date()!=today:
                text = u'技大発の次のバスは%d:%02d発、%d:%02d長岡駅着。今日の最終バス！これを逃すと次は明日の%d:%02d発、%d:%02d着だよ。' % (
                    next_start[0].hour, next_start[0].minute, next_start[1].hour, next_start[1].minute,
                    next_next_start[0].hour, next_next_start[0].minute, next_next_start[1].hour, next_next_start[1].minute)
            else:
                text = u'技大発の次のバスは%d:%02d発、%d:%02d長岡駅着。これを逃すと次は%d:%02d発、%d:%02d着だよ。' % (
                    next_start[0].hour, next_start[0].minute, next_start[1].hour, next_start[1].minute,
                    next_next_start[0].hour, next_next_start[0].minute, next_next_start[1].hour, next_next_start[1].minute)
        else:
            busiter = BusIterator(station_time_table, now)
            next_start = next(busiter)
            next_next_start = next(busiter)
            text = u''
            if next_start[0].date()!=today:
                text += u'長岡駅発の最終バスは行ってしまいました。次のバスは明日の%sだよ。' % self._from_station(next_start)
            else:
                text += u'長岡駅発の次のバスは%s。' % self._from_station(next_start)
                if next_start[1]:
                    if next_start[0].hour>=19:
                        text += u'技大着の最終だよ。急げー！'
                else:
                    text += u'技大前には止まりません。'
                if next_next_start[0].date()!=today:
                    text += u'今日の最終バス！これを逃すと次は明日の%sだよ。' % self._from_station(next_next_start)
                else:
                    text += u'これを逃すと次は%sだよ。' % self._from_station(next_next_start)
        return text

    def _from_station(self, times):
        text = u'%d:%02d発、' % (times[0].hour, times[0].minute)
        if times[1]:
            #技大前停車
            text += u'%d:%02d技大着' % (times[1].hour, times[1].minute)
        elif times[2]:
            #長峰団地で最終
            text += u'最終長峰団地'
        else:
            #技大入り口で停車
            text += u'技大入口停車'
        return text

def main():
    bus = Bus()
    arg = [int(s) for s in sys.argv[1:]]
    time = datetime.datetime(*arg)
    print time
    print bus.get_message(u'技大発のバスの時刻', time)
    print bus.get_message(u'駅発のバスの時刻', time)

if __name__=='__main__':
    main()
