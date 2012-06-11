# -*- coding:utf-8 -*-

# ユニコードデータベースへのアクセスを提供する

import re
import unicodedata

re_name = re.compile(ur'(\\[uU][0-9a-fA-F]{4}|[uU]\+[0-9a-fA-F]{4}|.)の文?字の名前')
re_tocodepoint = re.compile(ur'(.*)のコードポイント')
re_codepoint = re.compile(ur'[uU]\+([0-9a-fA-F]{4})の文?字')
re_mention = re.compile(ur'@\w+')

def hook(bot, status):
    text = re_mention.sub('', status.text).strip()

    m = re_name.search(text)
    if m:
        ch = m.group(1)
        if len(ch)>=6:
            ch = unichr(int(ch[2:], 16))
        name = unicodedata.name(ch)
        bot.reply_to(u'「%s」の名前は「%s」 [%s]' % (ch, name, bot.get_timestamp()), status)
        return True

    m = re_tocodepoint.search(text)
    if m:
        bot.reply_to(', '.join('U+%04X' % ord(ch) for ch in m.group(1)) + ' [%s]' % bot.get_timestamp(), status)
        return True

    m = re_codepoint.search(text)
    if m:
        ch = int(m.group(1), 16)
        bot.reply_to(u'U+%04Xは「%s」 [%s]' % (ch, unichr(ch), bot.get_timestamp()), status)
        return True
