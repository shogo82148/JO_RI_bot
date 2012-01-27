#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
//_/
//_/  CopyRight(C) K.Tsunoda(AddinBox) 2001 All Rights Reserved.
//_/  ( http://www.h3.dion.ne.jp/~sakatsu/index.htm )
//_/
//_/    この祝日判定コードは『Excel:kt関数アドイン』で使用しているものです。
//_/    この関数では、２００７年施行の改正祝日法(昭和の日)までを
//_/  　サポートしています(９月の国民の休日を含む)。
//_/
//_/  (*1)このコードを引用するに当たっては、必ずこのコメントも
//_/      一緒に引用する事とします。
//_/  (*2)他サイト上で本マクロを直接引用する事は、ご遠慮願います。
//_/      【 http://www.h3.dion.ne.jp/~sakatsu/holiday_logic.htm 】
//_/      へのリンクによる紹介で対応して下さい。
//_/  (*3)[ktHolidayName]という関数名そのものは、各自の環境に
//_/      おける命名規則に沿って変更しても構いません。
//_/  
//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

 追記 SETOGUCHI Mitsuhiro      http://straitmouth.jp/

 * 2007/May/26
 このスクリプトは JavaScript 用判定コード
  http://www.h3.dion.ne.jp/~sakatsu/holiday_logic.htm#JS
 を元に、Python 向けに移植したものです。

 holiday_name() は、年、月、日の3つの整数の引数を取ります。
 不適切な値を与えると、 ValueError が発生します。
 与えた日付が日本において何らかの祝日であれば、その名前が Unicode で返ります。
 祝日でない場合は None が返ります。

 * 2010/Sep/21
 holiday_name() にキーワード引数として datetime.date のオブジェクトも取れる
 ようにしました。これを指定する際は年、月、日は指定する必要がなく、指定しても
 無視されます。これにより、 jholiday モジュールを使用するスクリプトがすでに
 datetime.date のオブジェクトがある場合の効率が若干良くなります。

 holiday_name() は、指定した日が祝日であれば 
   Python 2.x 以前の場合は Unicode 文字列を、 
   Python 3.x 以降の場合は文字列を
 返します。指定した日が祝日でなければ、 Python のバージョンによらず None を返します。


サンプル

Python 2.6.1 (r261:67515, Feb 11 2010, 15:47:53) 
[GCC 4.2.1 (Apple Inc. build 5646)] on darwin
Type "help", "copyright", "credits" or "license" for more information.

>>> import jholiday
>>> jholiday.holiday_name(2007, 4, 28)
None
>>> jholiday.holiday_name(2007, 4, 29)
u'\u662d\u548c\u306e\u65e5'
>>> print jholiday.holiday_name(2007, 4, 29).encode('euc-jp')
昭和の日
>>> import datetime
>>> date = datetime.date(2007, 4, 29)
>>> jholiday.holiday_name(date = date)
u'\u662d\u548c\u306e\u65e5'


Python 3.1.2 (r312:79360M, Mar 24 2010, 01:33:18) 
[GCC 4.0.1 (Apple Inc. build 5493)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import jholiday
>>> jholiday.holiday_name(2007, 4, 28)
>>> jholiday.holiday_name(2007, 4, 29)
'昭和の日'
>>> print(jholiday.holiday_name(2007, 4, 29))
昭和の日
>>> import datetime
>>> date = datetime.date(2007, 4, 29)
>>> jholiday.holiday_name(date = date)
'昭和の日'
"""


import datetime
import sys

MONDAY, TUESDAY, WEDNESDAY = 0, 1, 2

def _vernal_equinox(y):
    """整数で年を与えると、その年の春分の日が3月の何日であるかを返す
"""
    if y <= 1947:
        d = 0
    elif y <= 1979:
        d = math.floor(20.8357  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    elif y <= 2099:
        d = math.floor(20.8431  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    elif y <= 2150:
        d = math.floor(21.8510  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    else:
        d = 0

    return d

def _autumn_equinox(y):
    """整数で年を与えると、その年の秋分の日が9月の何日であるかを返す
"""
    if y <= 1947:
        d = 0
    elif y <= 1979:
        d = math.floor(23.2588  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    elif y <= 2099:
        d = math.floor(23.2488  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    elif y <= 2150:
        d = math.floor(24.2488  +  0.242194 * (y - 1980)  -  math.floor((y - 1980) / 4))
    else:
        d = 0

    return d

def holiday_name(year = None, month = None, day = None, date = None):
    """holiday_name() の呼び出し方法は2通りあります。

    1つ目の方法は、3つの引数 year, month, day に整数を渡す方法です。
    もうひとつの方法は前述のキーワード引数 date に datetime.date のオブジェクトを渡す方法です。
    この場合は year, month, day を渡す必要はなく、また、渡したとしても無視されます。

    holiday_name() は、その日が祝日であれば 
        Python 2.x 系以前の場合には Unicode 文字列で
        Python 3.x 系以降の場合には文字列で
    祝日名を返します。
    指定した日が祝日でなければ、 Python のバージョンによらず None を返します。
"""

    if date == None:
        date = datetime.date(year, month, day)

    if date < datetime.date(1948, 7, 20):
        return None
    else:
        name = None


    # 1月
    if date.month == 1:
        if date.day == 1:
            name = '元日'
        else:
            if date.year >= 2000:
                if int((date.day - 1) / 7) == 1 and date.weekday() == MONDAY:
                    name = '成人の日'
            else:
                if date.day == 15:
                    name = '成人の日'
    # 2月
    elif date.month == 2:
        if date.day == 11 and date.year >= 1967:
            name = '建国記念の日'
        elif (date.year, date.month, date.day) == (1989, 2, 24):
            name = '昭和天皇の大喪の礼'
    # 3月
    elif date.month == 3:
        if date.day == _vernal_equinox(date.year):
            name = '春分の日'
    # 4月
    elif date.month == 4:
        if date.day == 29:
            if date.year >= 2007:
                name = '昭和の日'
            elif date.year >= 1989:
                name = 'みどりの日'
            else:
                name = '天皇誕生日'
        elif (date.year, date.month, date.day) == (1959, 4, 10):
            name = '皇太子明仁親王の結婚の儀'
    # 5月
    elif date.month == 5:
        if date.day == 3:
            name = '憲法記念日'
        elif date.day == 4:
            if date.year >= 2007:
                name = 'みどりの日'
            elif date.year >= 1986 and date.weekday() != MONDAY:
                name = '国民の休日'
        elif date.day == 5:
            name = 'こどもの日'
        elif date.day == 6:
            if date.year >= 2007 and date.weekday() in (TUESDAY, WEDNESDAY):
                name = '振替休日'
    # 6月
    elif date.month == 6:
        if (date.year, date.month, date.day) == (1993, 6, 9):
            name = '皇太子徳仁親王の結婚の儀'
    # 7月
    elif date.month == 7:
        if date.year >= 2003:
            if int((date.day - 1) / 7) == 2 and date.weekday() == MONDAY:
                name = '海の日'
        elif date.year >= 1996 and date.day == 20:
            name = '海の日'
    # 8月 (祝日なし)
    # 9月
    elif date.month == 9:
        autumn_equinox = _autumn_equinox(date.year)
        if date.day == autumn_equinox:
            name = '秋分の日'
        else:
            if date.year >= 2003:
                if int((date.day - 1) / 7) == 2 and date.weekday() == MONDAY:
                    name = '敬老の日'
                elif date.weekday() == TUESDAY and date.day == autumn_equinox - 1:
                    name = '国民の休日'
            elif date.year >= 1966 and date.day == 15:
                name = '敬老の日'
    # 10月
    elif date.month == 10:
        if date.year >= 2000:
            if int((date.day - 1) / 7) == 1 and date.weekday() == MONDAY:
                name = '体育の日'
        elif date.year >= 1966 and date.day == 10:
            name = '体育の日'
    # 11月
    elif date.month == 11:
        if date.day == 3:
            name = '文化の日'
        elif date.day == 23:
            name = '勤労感謝の日'
        elif (date.year, date.month, date.day) == (1990, 11, 12):
            name = '即位礼正殿の儀'
    # 12月
    elif date.month == 12:
        if date.day == 23 and date.year >= 1989:
            name = '天皇誕生日'

    # 振替休日
    if not name and date.weekday() == MONDAY:
        prev = date + datetime.timedelta(days = -1)
        if holiday_name(prev.year, prev.month, prev.day):
            name = '振替休日'

    if name and sys.version_info[0] < 3:
        name = unicode(name, 'utf-8')

    return name


"""
//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
//_/ CopyRight(C) K.Tsunoda(AddinBox) 2001 All Rights Reserved.
//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
"""
