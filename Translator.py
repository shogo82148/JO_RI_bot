#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
翻訳をするライブラリ
"""

import urllib
import re
from xml.sax.saxutils import unescape
class Translator(object):
    _base_url = 'http://api.microsofttranslator.com/V2/Http.svc/Translate'
    _re_string = re.compile(r'<string\s+xmlns="[^"]+">(.*)</string>')
    _lang_dict = {
        u'アラビア':'ar', u'亜': 'ar',
        u'イタリア':'it', u'伊': 'it',
        u'インドネシア':'id',
        u'ウクライナ':'uk', 
        u'エストニア':'et',
        u'オランダ': 'nl', u'蘭': 'nl',
        u'カタロニア': 'ca', u'カタルーニャ': 'ca',
        u'ギリシャ': 'el', u'ギリシア': 'el',
        u'スウェーデン': 'sv',
        u'スペイン': 'es', u'カスティーリャ': 'es',
        u'スロバキア': 'sk', u'スロヴァキア': 'sk',
        u'スロベニア': 'sl',
        u'タイ': 'th',
        u'チェコ': 'cs',
        u'デンマーク': 'da',
        u'ドイツ': 'de', u'独': 'de',
        u'トルコ': 'tr',
        u'ノルウェー': 'no',
        u'ハイチ': 'ht',
        u'ハンガリー': 'hu', u'マジャル': 'hu',
        u'ヒンディー': 'hi',
        u'フィンランド': 'fi', u'スミオ': 'fi', u'フィン': 'fi',
        u'フランス': 'fr', u'仏': 'fr',
        u'ブルガリア': 'bg',
        u'ベトナム': 'vi', u'キン': 'vi', u'安南': 'vi',
        u'ヘブライ': 'he',
        u'ポーランド': 'pl', u'波': 'pl',
        u'ポルトガル': 'pt',
        u'ラトビア': 'lv', u'レット': 'lv',
        u'リトアニア': 'lt',
        u'ルーマニア': 'ro',
        u'ロシア': 'ru',
        u'英': 'en', u'米': 'en',
        u'簡体字中国': 'zh-CHS', u'中国': 'zh-CHS',
        u'韓国': 'ko', u'朝鮮': 'ko',
        u'日本': 'ja', u'和': 'ja',
        u'繁体字中国': 'zh-CHT',
        }
    _re_retweet = re.compile(ur'[QR]T\s+@?\w+:\s+(.*)', re.IGNORECASE)
    _re_mention = re.compile(ur'@\w+')

    def __init__(self, appId, lang_from=None, lang_to='ja'):
        self.lang_from = lang_from
        self.lang_to = lang_to
        self.appId = appId

        #リプライ用の正規表現作成
        lang_list = self._lang_dict.keys() + self._lang_dict.values()
        lang = '|'.join(lang_list)
        self._re_translate_text = re.compile(ur'^(.*)を(%s)語?訳' % lang, re.IGNORECASE)
        self._re_translate = re.compile(ur'(%s)語?訳' % lang, re.IGNORECASE)

    def translate(self, text, lang_from=None, lang_to=None):
        arg = {}
        arg['appId'] = self.appId
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        arg['text'] = text
        arg['to'] = lang_to or self.lang_to
        if lang_from or self.lang_from:
            arg['from'] = lang_from or self.lang_from
        url = self._base_url + '?' + urllib.urlencode(arg)
        res = urllib.urlopen(url).read().decode('utf-8')
        m = self._re_string.match(res)
        if not m:
            return None
        return unescape(m.group(1))

    def hook(self, bot, status):
        m = self._re_translate_text.search(status.text)
        if m:
            text = m.group(1)
            lang = m.group(2)
            text = self._re_mention.sub('', text)
            bot.reply_to(self.translate(text, None, self._lang_dict.get(lang, lang)), status)
            return True
        m = self._re_translate.search(status.text)
        if m:
            lang = m.group(1)
            m = self._re_retweet.search(status.text)
            if m:
                #RTされた文章を翻訳
                text = m.group(1)
            elif status.in_reply_to_status_id:
                #リプライを飛ばした先の文章を翻訳
                reply_to_status = bot.api.get_status(status.in_reply_to_status_id)
                text = reply_to_status.text
            text = self._re_mention.sub('', text)
            bot.reply_to(self.translate(text, None, self._lang_dict.get(lang, lang)), status)
            return True
        return False
