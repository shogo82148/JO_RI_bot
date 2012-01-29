#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib
import lxml.etree
import re
from Translator import Translator
import logging

logger = logging.getLogger("BaseBot")

class WolframAlpha(object):
    _base_url = 'http://api.wolframalpha.com/v2/query'
    def __init__(self, appId, translator=None):
        self.appId = appId
        self.translator = translator

    def ask(self, query):
        arg = {}
        arg['appid'] = self.appId
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        arg['input'] = query

        url = self._base_url + '?' + urllib.urlencode(arg)
        xml = urllib.urlopen(url).read()
        tree = lxml.etree.fromstring(xml)
        return tree

    def get_text(self, query):
        xml = self.ask(query)
        pods = xml.xpath('//pod')
        if len(pods)<2:
            return ''

        res = pods[0].attrib['title'] + ':'
        res += pods[0].xpath('.//plaintext/text()')[0] + '. '
        res += pods[1].attrib['title'] + ':'
        res += ', '.join(pods[1].xpath('.//plaintext/text()')[0].split('\n')) + '. '
        return res

    _re_tell_me = re.compile(ur'^@\w+\s+(.*?)(について|を|に関して)?教えて')
    _re_tell_me_en = re.compile(ur'@\w+\s+tell\s+me\s+(about\s+)?(.*?)\.?$', re.IGNORECASE)
    def hook(self, bot, status):
        query = ''
        translate_flag = False
        m = self._re_tell_me.search(status.text)
        if m:
            query = m.group(1)
            translate_flag = True
        else:
            m = self._re_tell_me_en.search(status.text)
            if m:
                query = m.group(2)
        if not query:
            return False

        logger.info(u'query:' + query)
        if translate_flag and self.translator:
            query = self.translator.translate(query, 'ja', 'en')
            logger.info(u'Translated:' + query)

        answer = self.get_text(query)
        if not answer:
            return False
        logger.info(u'Answer:' + answer)
        
        if translate_flag and self.translator:
            answer = self.translator.translate(answer, 'en', 'ja')
            logger.info(u'Translated:' + answer)
        
        limit = 140 - len('@%s ' % status.author.screen_name)
        limit -= 21 #For URL
        if len(answer)>limit:
            answer = answer[0:limit]
        answer += ' http://www.wolframalpha.com/input/?i=' + urllib.quote_plus(query)
        bot.reply_to(answer, status, cut=False)
        return True
