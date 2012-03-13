#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
翻訳をするライブラリ
"""

import urllib
import re
from xml.sax.saxutils import unescape
import TwitterBot.lib.Translator.Translator as LibTranslator
import logging

logger = logging.getLogger("Bot.Trans")

class Translator(object):
    _re_retweet = re.compile(ur'[QR]T\s+@?\w+:?\s+(.*)', re.IGNORECASE)
    _re_mention = re.compile(ur'@\w+')
    _re_detect = re.compile(ur'^(.*?)(って|は)?何語')

    def __init__(self, appId, lang_from=None, lang_to='ja'):
        self.translator = LibTranslator(appId, lang_from, lang_to)

        lang = '|'.join(self.translator.get_lang_list())
        self._re_translate_text = re.compile(ur'^(?P<text>.*[^語])を(:?(?P<from>%s)語から)?(?P<to>%s)(訳|語訳|語翻訳|語へ翻訳)' % (lang, lang), re.IGNORECASE)
        self._re_translate = re.compile(ur'(:?(?P<from>%s)語(:?を|から))?(?P<to>%s)(:?訳|語訳|語翻訳|語へ翻訳)' % (lang, lang), re.IGNORECASE)


    _re_timestamp = re.compile(ur'\[(.*?)\]')
    def rm_timestamp(self, text):
        return self._re_timestamp.sub(u'', text)

    def hook(self, bot, status):
        m = self._re_translate_text.search(status.text)
        if m:
            lang_from = m.group('from')
            lang_from = self.translator.lang2code(lang_from)
            lang_to = m.group('to')
            lang_to = self.translator.lang2code(lang_to)
            text = m.group('text')
            text = self.rm_timestamp(text)
            text = self._re_mention.sub('', text)
            text = self.translator.translate(text, lang_from, lang_to)
            text = u'[%s語訳]%s [%s]' % (self.translator.code2lang(lang_to), text, bot.get_timestamp())
            bot.reply_to(text, status)
            return True

        m = self._re_translate.search(status.text)
        if m:
            lang_from = m.group('from')
            lang_from = self.translator.lang2code(lang_from)
            lang_to = m.group('to')
            lang_to = self.translator.lang2code(lang_to)
            text = u'翻訳する文章を教えてください'
            m = self._re_retweet.search(status.text)
            if m:
                #RTされた文章を翻訳
                text = m.group(1)
            elif status.in_reply_to_status_id:
                #リプライを飛ばした先の文章を翻訳
                reply_to_status = bot.api.get_status(status.in_reply_to_status_id)
                text = reply_to_status.text
            text = self.rm_timestamp(text)
            text = self._re_mention.sub('', text)
            text = self.translator.translate(text, lang_from, lang_to)
            text = u'[%s語訳]%s [%s]' % (self.translator.code2lang(lang_to), text, bot.get_timestamp())
            bot.reply_to(text, status)
            return True

        m = self._re_detect.search(status.text)
        if m:
            text = m.group(1)
            m = self._re_retweet.search(status.text)
            if m:
                #RTされた文章を翻訳
                text = m.group(1)
            elif status.in_reply_to_status_id:
                #リプライを飛ばした先の文章を翻訳
                reply_to_status = bot.api.get_status(status.in_reply_to_status_id)
                text = reply_to_status.text
            text = self.rm_timestamp(text)
            text = self._re_mention.sub('', text)
            lang = self.translator.detect(text)
            if lang:
                bot.reply_to(u'それは%s語だね [%s]' % (self.translator.code2lang(lang), bot.get_timestamp()), status)
            else:
                bot.reply_to(u'ワカラナイ [%s]' % bot.get_timestamp(), status)
            return True

        return False
