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
        self._re_translate_text = re.compile(ur'^(.*)を(%s)(訳|語訳|語翻訳)' % lang, re.IGNORECASE)
        self._re_translate = re.compile(ur'(%s)(訳|語訳|語翻訳)' % lang, re.IGNORECASE)

    def hook(self, bot, status):
        m = self._re_translate_text.search(status.text)
        if m:
            text = m.group(1)
            lang = m.group(2)
            text = self._re_mention.sub('', text)
            bot.reply_to(self.translator.translate(text, None, self.translator.lang2code(lang)), status)
            return True

        m = self._re_translate.search(status.text)
        if m:
            lang = m.group(1)
            text = u'翻訳する文章を教えてください'
            m = self._re_retweet.search(status.text)
            if m:
                #RTされた文章を翻訳
                text = m.group(1)
            elif status.in_reply_to_status_id:
                #リプライを飛ばした先の文章を翻訳
                reply_to_status = bot.api.get_status(status.in_reply_to_status_id)
                text = reply_to_status.text
            text = self._re_mention.sub('', text)
            bot.reply_to(u'[%s語訳]%s [%s]' % (
                    self.translator._inverse_lang_dict.get(lang, lang),
                    self.translator.translate(text, None, self.translator._lang_dict.get(lang, lang)),
                    bot.get_timestamp()), status)
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
            text = self._re_mention.sub('', text)
            lang = self.translator.detect(text)
            if lang:
                bot.reply_to(u'それは%s語だね [%s]' % (self.translator.code2lang(lang), bot.get_timestamp()), status)
            else:
                bot.reply_to(u'ワカラナイ [%s]' % bot.get_timestamp(), status)
            return True

        return False
