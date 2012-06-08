#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
アマゾン連携プログラム
"""

import sys
import codecs
import urllib
import urllib2
import datetime
import re
import lxml.etree
import lxml.html
import bottlenose
import random
import itertools
import logging
import unicodedata

logger = logging.getLogger("Bot.amazon")
namespaces={'ns':"http://webservices.amazon.com/AWSECommerceService/2011-08-01"}

class Result(object):
    def __init__(self, xml):
        self.tree = lxml.etree.fromstring(xml)
        self.items = self.tree.xpath('//ns:Item', namespaces = namespaces)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        item = self.items[key]
        isbn = item.xpath('.//ns:ASIN/text()', namespaces = namespaces)[0]
        item_dict = {}
        item_dict['isbn'] = isbn
        item_dict['title'] = item.xpath('.//ns:Title/text()', namespaces = namespaces)[0]
        item_dict['detailURL'] = item.xpath('.//ns:DetailPageURL/text()', namespaces=namespaces)[0]
        item_dict['links'] = dict(zip(
                item.xpath('.//ns:Description/text()', namespaces = namespaces),
                item.xpath('.//ns:URL/text()', namespaces = namespaces),
                ))
        return item_dict

    def geturl(self):
        return self.tree.xpath('//ns:MoreSearchResultsUrl/text()', namespaces = namespaces)[0]

class Tweet(object):
    def __init__(self, result, no=0):
        self.result = result
        self.no = no

    def reply_to(self, bot, status):
        msg = random.choice(Amazon.messages)
        if len(self.result)==0:
            bot.reply_to(
                u'%s http://www.amazon.co.jp/ [%s]' % (msg, bot.get_timestamp()), status)
        elif self.no < len(self.result):
            item = self.result[self.no]
            url = item['detailURL']
            msg += ':'
            timestamp = " [%s]" % bot.get_timestamp()
            title = item['title']

            limit = 140 - len('@%s ' % status.author.screen_name)
            limit -= len(msg)
            limit -= 21 # For space and url
            if len(title)>limit:
                title = title[0:limit-1] + u'…'
            new_status = bot.reply_to(u'%s%s %s%s' % (msg, title, url, timestamp), status, cut=False)
            bot.append_reply_hook(self.hook, name='amazon-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)
        else:
            bot.reply_to(u'後は自分で探せ %s [%s]' % (self.result.geturl(), bot.get_timestamp()), status, cut=False)

        return True

    def update_detail(self, bot, status):
        bot.reply_to(u'ほい %s [%s]' % (self.result.geturl(), bot.get_timestamp()), status, cut=False)
        return

    re_other = re.compile(u'ほか|他|違う|ちがう|別|べつ')
    re_detail = re.compile(u'検索結果')
    def hook(self, bot, status):
        if self.no>=len(self.result):
            return

        m = self.re_other.search(status.text)
        if m:
            r = Tweet(self.result, self.no+1)
            r.reply_to(bot, status)
            return True

        m = self.re_detail.search(status.text)
        if m:
            self.update_detail(bot, status)
            return True

        return


class Amazon(object):
    searchIndexDic = {
        u'すべて': 'All',
        u'服': 'Apparel',
        u'洋服': 'Apparel',
        u'衣服': 'Apparel',
        u'アクセ': 'Apparel',
        u'アクセサリ': 'Apparel',
        u'アクセサリー': 'Apparel',
        u'化粧品': 'Beauty',
        u'本': 'Books',
        u'和書': 'Books',
        u'クラシック': 'Classical',
        u'クラシック音楽': 'Classical',
        u'dvd': 'DVD',
        u'パソコン': 'Electronics',
        u'家電': 'Electronics',
        u'カメラ': 'Electronics',
        u'デジカメ': 'Electronics',
        u'デジイチ': 'Electronics',
        u'コンデジ': 'Electronics',
        u'レコーダ': 'Electronics',
        u'携帯電話': 'Electronics',
        u'ケータイ': 'Electronics',
        u'洋書': 'ForeignBooks',
        u'食べ物': 'Grocery',
        u'食品': 'Grocery',
        u'飲み物': 'Grocery',
        u'食い物': 'Grocery',
        u'宝石': 'Jewelry',
        u'貴金属': 'Jewelry',
        u'キッチン用品': 'Kitchen',
        u'マーケットプレイス': 'Marketplace',
        u'中古品': 'Marketplace',
        u'mp3': 'MP3Downloads',
        u'音楽': 'Music',
        u'楽曲': 'Music',
        u'ミュージック': 'Music',
        u'楽器': 'MusicalInstruments',
        u'文具': 'OfficeProducts',
        u'文房具': 'OfficeProducts',
        u'ソフト': 'Software',
        u'靴': 'Shoes',
        u'ソフトウェア': 'Software',
        u'おもちゃ': 'Toys',
        u'玩具': 'Toys',
        u'ビデオ': 'Video',
        u'アニメ': 'Video',
        u'bd': 'Video',
        u'tvゲーム': 'VideoGames',
        u'テレビゲーム': 'VideoGames',
        u'時計': 'Watches',
        }

    messages = [
        u'IYH!!',
        u'今すぐ買え！',
        u'買え！',
        u'イヤッッホォォォオオォオウ！！',
        ]

    def __init__(self, user_name, user, access_key, secret_key, tag):
        self._user = user
        self._user_name = user_name
        self._amazon = bottlenose.Amazon(
            access_key, secret_key, Region='JP')
        self._associate_tag = tag

        indexes = u'(?P<index>%s)' % '|'.join(Amazon.searchIndexDic.iterkeys())
        keyword = u'(?P<keyword>.*?)'
        buy = u'(?:(?:買う|購入する?|iyhする?|買収する?)べき|(?:買った|購入した|iyhした|買収した)ほうがいい|欲しい|ほしー)'
        self._re_hook = re.compile(ur'^%s(:?(?:の|な)%s)?(?:って|を|が)?%s' % (keyword, indexes, buy), re.I)

    def search(self, keywords, page=1, index='All'):
        res = self._amazon.ItemSearch(
            Keywords=keywords,
            SearchIndex=index,
            ItemPage=str(page),
            ResponseGroup='Small',
            AssociateTag=self._associate_tag)
        xml = res.decode('utf-8')
        return Result(xml)

    _re_mention = re.compile(ur'@\w+')
    def hook(self, bot, status):
        text = self._re_mention.sub('', status.text)
        text = unicodedata.normalize('NFKC', text)
        text = text.lower()
        m = self._re_hook.search(text)
        if not m:
            return False

        keyword = m.group('keyword').strip()
        index = Amazon.searchIndexDic.get(m.group('index') or 'すべて', 'All')
        logger.debug('Keyword: %s, SearchIndex: %s', keyword, index)
        tweet = Tweet(self.search(keyword, index=index))
        tweet.reply_to(bot, status)
        return True


