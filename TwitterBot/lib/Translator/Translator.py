#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
翻訳をするライブラリ
"""

import urllib
import re
from xml.sax.saxutils import unescape
import Misakurago
import Ondulish
import Grongish
import Lou
import logging
import Ika
import Enteisla
import Sizuka

logger = logging.getLogger("Bot.Trans")

class Translator(object):
    _base_url = 'http://api.microsofttranslator.com/V2/Http.svc/'
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
        u'イカ娘': 'ikamusume',
        u'みさくら': 'misakura',
        u'オンドゥル': 'ondulish',
        u'ルー': 'lou',
        u'オンドゥルー': 'ondulishlou',
        u'グロンギ': 'grongish',
        u'エンテイスラ': 'enteisla',
        u'しずかったー': 'sizuka',
        u'折り返し翻': 'orikaeshi',
        }

    def __init__(self, appId, lang_from=None, lang_to='ja'):
        self.lang_from = lang_from
        self.lang_to = lang_to
        self.appId = appId
        self.ika = Ika.Ika()
        self.misakurago = Misakurago.Misakurago()
        self.ondulish = Ondulish.Ondulish()
        self.grongish = Grongish.Grongish(dic='dic/Grongish')
        self.enteisla = Enteisla.Enteisla()
        self.sizuka = Sizuka.Sizuka()

        #言語コード対名前辞書を作成
        inverse_lang_dict = {}
        for name, lang in self._lang_dict.iteritems():
            old_name = inverse_lang_dict.get(lang, '')
            if len(name)>len(old_name):
                inverse_lang_dict[lang] = name
        self._inverse_lang_dict = inverse_lang_dict

    def lang2code(self, lang):
        """ 言語名を言語コードに変換する """
        return self._lang_dict.get(lang, lang)

    def code2lang(self, code):
        """ 言語コードを言語名に変換する """
        return self._inverse_lang_dict.get(code, code)

    def get_lang_list(self):
        return self._lang_dict.keys() + self._lang_dict.values()

    def _translateBing(self, text, lang_from=None, lang_to=None):
        logger.debug(u'Translating with Bing')
        logger.debug(u'Text: %s' % text)
        arg = {}
        arg['appId'] = self.appId
        text = text.replace('\n', '').replace('\r', '')
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        arg['text'] = text
        arg['to'] = lang_to or self.lang_to
        if lang_from or self.lang_from:
            arg['from'] = lang_from or self.lang_from
        url = self._base_url + 'Translate?' + urllib.urlencode(arg)
        res = urllib.urlopen(url).read().decode('utf-8')
        m = self._re_string.match(res)
        if not m:
            return None

        text = unescape(m.group(1))
        logger.debug(u'Result: %s' % text)
        return text

    def detect(self, text):
        if self.sizuka.detect(text):
            return 'sizuka'
        if self.ika.detect(text):
            return 'ikamusume'
        if self.misakurago.detect(text):
            return 'misakura'
        if self.ondulish.detect(text):
            return 'ondulish'
        if self.grongish.detect(text):
            return 'grongish'
        if self.enteisla.detect(text):
            return 'enteisla'
        arg = {}
        arg['appId'] = self.appId
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        arg['text'] = text
        url = self._base_url + 'Detect?' + urllib.urlencode(arg)
        res = urllib.urlopen(url).read().decode('utf-8')
        m = self._re_string.match(res)
        if not m:
            return None
        return unescape(m.group(1))

    def translate(self, text, lang_from=None, lang_to=None):
        lang_from = lang_from or self.lang_from
        lang_to = lang_to or self.lang_to
        if lang_from=='sizuka' or self.sizuka.detect(text):
            text = self.sizuka.antitranslate(text)
            lang_from = 'ja'
        elif lang_from=='grongish' or self.grongish.detect(text):
            text = self.grongish.grtranslate(text)
            lang_from = 'ja'
        elif lang_from=='enteisla' or self.enteisla.detect(text):
            text = self.translate(text)
            lang_from = 'ja'

        if lang_to=='ikamusume':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            return self.ika.translate(text)
        elif lang_to=='misakura':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            return self.misakurago.translate(text)
        elif lang_to=='ondulish':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            return self.ondulish.translate(text)
        elif lang_to=='lou':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            return Lou.Lou().translate(text)
        elif lang_to=='ondulishlou':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            text = Lou.Lou().translate(text)
            return Ondulish.Ondulish().translate(text)
        elif lang_to=='grongish':
            if lang_from!='ja':
                text = self._translateBing(text, lang_from, 'ja')
            return self.grongish.translate(text)
        elif lang_to=='enteisla':
            if lang_from!='en':
                text = self._translateBing(text, lang_from, 'en')
            return self.enteisla.translate(text)
        elif lang_to == 'sizuka':
            if lang_from != 'ja':
                text = self._translateBing(text, lang_from, 'ja')
            return self.sizuka.translate(text)
        elif lang_to == 'orikaeshi':
            return self._translateBing(self._translateBing(self._translateBing(self._translateBing(text, 'ja', 'en'), 'en', 'nl'), 'nl', 'it'), 'it', 'ja')
        else:
            return self._translateBing(text, lang_from, lang_to)

