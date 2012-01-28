#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
学食のメニューをツイートする
"""

import xml.etree.ElementTree as ElementTree
import sys
import codecs
import urllib
import gdata.spreadsheet.text_db
import datetime
import re
import random

class GakuShoku(object):
    def __init__(self, mail, password, menu_id, menu_sheet):
        self._lunch_end = datetime.time(14, 0, 0)
        self._dinner_end = datetime.time(19, 0, 0)
        self.client = gdata.spreadsheet.text_db.DatabaseClient(mail, password)
        self.db = self.client.GetDatabases(menu_id)[0]
        self.tbl = self.db.GetTables(menu_sheet)[0]
        self.random = random.Random()

    def get_menu(self, date=None, year=None, month=None, day=None):
        if date:
            year = date.year
            month = date.month
            day = date.day
        query = u'date==%04d/%02d/%02d' % (year, month, day)
        records = self.tbl.FindRecords(query)
        if len(records)==0:
            return None
        return records[0].content

    _re_menu = re.compile(u'[メめﾒ][ニにﾆ][ュゅｭ]|menu|[昼晩夕]食|めし|ごはん|飯|[abc]定|学食'
                          u'|(腹|なか|はら).*(減った|へった|すいた|空いた)'
                          u'|[フふﾌ][ンんﾝ](ガ|が|ｶﾞ)'
                          u'|はらへ')
    _re_today = re.compile(u'今日|きょう')
    _re_tomorrow = re.compile(u'明日|翌日|あした|よくじつ')
    _re_after_tomorrow = re.compile(u'明後日|あさって|みょうごにち')
    _re_set_menu = re.compile(u'[セせｾ][ッっｯ][トとﾄ]|丼|麺|(ド|ど|ﾄﾞ)[ンんﾝ]|[メめﾒ][ンんﾝ]')
    _re_item = re.compile(u'単品')
    _re_mention = re.compile(r'@\w+')
    def find(self, query):
        query = query.lower()
        query = self._re_mention.sub('', query)
        if not self._re_menu.search(query):
            return ''

        date = None
        is_dinner = None

        #昼食 or 夕食?
        if query.find(u'昼')>=0:
            is_dinner = False
        elif query.find(u'晩')>=0 or query.find(u'夕')>=0:
            is_dinner = True

        #日付は？
        if self._re_today.search(query):
            date = datetime.datetime.today()
            if is_dinner is None:
                is_dinner = (date.time()>self._lunch_end)
        elif self._re_tomorrow.search(query):
            date = datetime.datetime.today() + datetime.timedelta(1)
        elif self._re_after_tomorrow.search(query):
            date = datetime.datetime.today() + datetime.timedelta(2)
        else:
            date = datetime.datetime.today()
            if is_dinner is None:
                if date.time()>self._dinner_end:
                    date += datetime.timedelta(1)
                    is_dinner = False
                else:
                    is_dinner = (date.time()>self._lunch_end)

        menu = self.get_menu(date)
        if not menu:
            return u'404 not found'

        if query.find(u'a')>=0:
            if query.find(u'週替')>=0:
                return self._teishoku(menu, is_dinner, u'週替わりa')
            else:
                return self._teishoku(menu, is_dinner, u'a')
        elif query.find(u'b')>=0:
            return self._teishoku(menu, is_dinner, u'b')
        elif query.find(u'c')>=0:
            return self._teishoku(menu, is_dinner, u'c')
        elif self._re_set_menu.search(query):
            return self._set_menu(menu, is_dinner)
        elif self._re_item.search(query):
            return self._items(menu, is_dinner)

        return self._recommend(menu, is_dinner)

    def _teishoku(self, menu, is_dinner, dish_type):
        """定食メニューを返す"""
        dish_time = (u'夕食' if is_dinner else u'昼食')
        date = menu[u'date']
        dish1 = menu.get(dish_time + dish_type + u'定食1', None)
        dish2 = menu.get(dish_time + dish_type + u'定食2', None)
        dish_type = dish_type.upper()

        if not dish1:
            return u'%sの%sの%s定食はありません' % (date, dish_time, dish_type)
        elif not dish2:
            return u'%sの%sの%s定食は、%sです' % (date, dish_time, dish_type, dish1)
        else:
            return u'%sの%sの%s定食は、%sと、%sです' % (date, dish_time, dish_type, dish1, dish2)
    
    def _set_menu(self, menu, is_dinner):
        """セットメニューを返す"""
        dish_time = (u'夕食' if is_dinner else u'昼食')
        date = menu[u'date']
        dish = menu.get(dish_time + u'セット', None)
        if dish:
            return u'%sの%sセットは、%sです' % (date, dish_time, dish)
        else:
            return u'%sの%sセットはありません' % (date, dish_time)

    def _items(self, menu, is_dinner):
        """単品メニューを返す"""
        dish_time = (u'夕食' if is_dinner else u'昼食')
        date = menu[u'date']
        dishes = []
        for i in range(1,6):
            dish = menu.get(dish_time + u'単品%d' % i, None)
            if dish:
                dishes.append(dish)

        if len(dishes)!=0:
            return u'%sの%s単品は、%sです' % (date, dish_time, u'・'.join(dishes))
        else:
            return u'%sの%s単品はありません' % (date, dish_time)

    def _recommend(self, menu, is_dinner):
        """おすすめを返す"""
        dish_time = (u'夕食' if is_dinner else u'昼食')
        date = menu[u'date']
        selections = []

        #A定食
        for dish_type in [u'a', u'b', u'c', u'日替わりa']:
            dish1 = menu.get(dish_time + dish_type + u'定食1', None)
            dish2 = menu.get(dish_time + dish_type + u'定食2', None)
            if dish1:
                if dish2:
                    selections.append(u'%sと%s(%s定食)' % (dish1, dish2, dish_type.upper()))
                else:
                    selections.append(u'%s(%s定食)' % (dish1, dish_type.upper()))

        #セットメニュー
        dish = menu.get(dish_time + u'セット', None)
        if dish:
            selections.append(dish)

        #単品メニュー
        for i in range(1,6):
            dish = menu.get(dish_time + u'単品%d' % i, None)
            if dish:
                selections.append(dish)

        #適当に推薦
        return u'%sの%sのおすすめは、%sです' % (
            date, dish_time,
            self.random.choice(selections))

    def hook(self, bot, status):
        text = self.find(status.text)
        if text:
            bot.reply_to(text + u' [%s]' % bot.get_timestamp(), status)
            return True
        else:
            return False

def main():    
    import config
    query = sys.argv[1].decode('utf-8')
    print GakuShoku(config.MENU_EMAIL, config.MENU_PASSWORD,
                config.MENU_ID, config.MENU_SHEET).find(query) + u' [%s]' % datetime.datetime.today().ctime()

if __name__=="__main__":
    sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    main()

