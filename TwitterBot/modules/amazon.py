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
import sqlite3

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
        item_dict['asin'] = isbn
        item_dict['title'] = item.xpath('.//ns:Title/text()', namespaces = namespaces)[0]
        item_dict['detailURL'] = item.xpath('.//ns:DetailPageURL/text()', namespaces=namespaces)[0]
        item_dict['links'] = dict(zip(
                item.xpath('.//ns:Description/text()', namespaces = namespaces),
                item.xpath('.//ns:URL/text()', namespaces = namespaces),
                ))
        return item_dict

    def geturl(self):
        return self.tree.xpath('//ns:MoreSearchResultsUrl/text()', namespaces = namespaces)[0]

class Cart(object):
    def __init__(self, amazon, owner, CartId = None, HMAC = None):
        self._amazon = amazon
        self._CartId = CartId
        self._HMAC = HMAC
        self.owner = owner
        self.url = None

    def add(self, asin):
        karg = {}
        karg['Item.1.ASIN'] = asin
        karg['Item.1.Quantity'] = 1
        if self._CartId:
            logger.debug('Adding %s to cart(%s,%s)', asin, self._CartId, self._HMAC)
            karg['CartId'] = self._CartId
            karg['HMAC'] = self._HMAC
            xml = self._amazon.CartAdd(**karg)
        else:
            logger.debug('Creating new cart')
            xml = self._amazon.CartCreate(**karg)
        tree = lxml.etree.fromstring(xml)
        msg = tree.xpath('//ns:Message/text()', namespaces=namespaces)
        if len(msg)>0:
            logger.error('Error: %s', msg[0])
            return False
        self.url = tree.xpath('//ns:PurchaseURL/text()', namespaces=namespaces)[0]
        self._CartId = tree.xpath('//ns:CartId/text()', namespaces=namespaces)[0]
        self._HMAC = tree.xpath('//ns:HMAC/text()', namespaces=namespaces)[0]
        return True

class TweetBuy(object):
    def __init__(self, asin, amazon, cart=None):
        self._asin = asin
        self._amazon = amazon
        self.cart = cart
        return

    def similar(self, asin):
        res = self._amazon.SimilarityLookup(
            ItemId = asin
            )
        xml = res.decode('utf-8')
        return Result(xml)

    def buy(self, bot, status):
        cart = self.cart
        if cart is None or cart.owner != status.author.screen_name:
            cart = Cart(self._amazon, status.author.screen_name)
            if cart.add(self._asin):
                text = u'お買い上げありがとうございます！商品はこちらのURLからご購入いただけます。 %s [%s]' % (cart.url, bot.get_timestamp())
                bot.api.send_direct_message(user=status.author.id, text=text)
                self.cart = cart
                return True
            return False
        else:
            return cart.add(self._asin)

    def reply_to(self, bot, status, msg=None, failmsg=None):
        msg = msg or u'お買い上げありがとうございます！この商品を買った人はこんな商品も買っています'
        res = self.similar(self._asin)
        if len(res)==0:
            msg = failmsg or u'お買い上げありがとうございます！'
        r = Tweet(res, amazon=self._amazon, cart=self.cart, msg=msg)
        r.reply_to(bot, status)
        return True

class Tweet(object):
    def __init__(self, result, no=0, amazon=None, cart=None, msg=None):
        self.result = result
        self.no = no
        self._amazon = amazon
        self._cart = cart
        self._msg = msg

    def reply_to(self, bot, status):
        msg = self._msg or random.choice(Amazon.messages)
        if len(self.result)==0:
            bot.reply_to(
                u'%s http://www.amazon.co.jp/ [%s]' % (msg, bot.get_timestamp()), status)
        elif self.no < len(self.result):
            item = self.result[self.no]
            url = item['detailURL']
            msg += ':'
            timestamp = " [%s]" % bot.get_timestamp()
            title = item['title']

            short_url_length = bot.configure.get(u'short_url_length', 20)
            limit = bot.tweet_length - len('@%s ' % status.author.screen_name)
            limit -= len(msg)
            limit -= short_url_length + 1 # For space and url
            limit -= len(timestamp)
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

    re_relation = re.compile(u'(?:関連)')
    re_buy = re.compile(u'(?:それ|その|そんな).*(?:買|購入|iyh|欲)')
    re_other = re.compile(u'ほか|他|違う|ちがう|別|べつ')
    re_detail = re.compile(u'検索結果')
    def hook(self, bot, status):
        if self.no>=len(self.result):
            return

        text = unicodedata.normalize('NFKC', status.text)
        text = text.lower()

        m = self.re_buy.search(text)
        if m:
            r = TweetBuy(self.result[self.no]['asin'], self._amazon, cart=self._cart)
            if r.buy(bot, status):
                r.reply_to(bot, status)
            else:
                r.reply_to(bot, status, msg=u'在庫が無いみたい。こんな商品はいかが？', failmsg=u'在庫が無いみたい。')
            return True

        m = self.re_relation.search(text)
        if m:
            r = TweetBuy(self.result[self.no]['asin'], self._amazon, cart=self._cart)
            r.reply_to(bot, status, msg=u'この商品を買った人はこんな商品も買っています', failmsg=u'関連商品が見つからなかったよ')
            return True

        m = self.re_other.search(text)
        if m:
            r = Tweet(self.result, no=self.no+1, amazon=self._amazon, cart=self._cart)
            r.reply_to(bot, status)
            return True

        m = self.re_detail.search(text)
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
            access_key, secret_key, Region='JP',
            AssociateTag = tag)

        indexes = u'(?P<index>%s)' % '|'.join(Amazon.searchIndexDic.iterkeys())
        keyword = u'(?P<keyword>.*?)'
        buy = u'(?:(?:買う|購入する?|iyhする?|買収する?)べき|(?:買った|購入した|iyhした|買収した)ほうがいい|欲しい|ほしー)'
        self._re_hook = re.compile(ur'^%s(:?(?:の|な)%s)?(?:って|を|が)?%s' % (keyword, indexes, buy), re.I)

        tellme = u'(?P<keyword>.*)の新刊が?[出で]たら(?:(?:教|おし)えて|(?:教|おし)えろ|[知し]らせて|[知し]らせろ)'
        self._re_tellme = re.compile(tellme)
        self._db_file = "amazon_tellme.sqlite3"

        con = None
        try:
            con = sqlite3.connect(self._db_file)
            con.execute(
                u'create table if not exists user_keywords('
                u'user_id varchar(100),'
                u'status_id varchar(100),'
                u'keyword varchar(100)'
                u');')
            con.execute(
                u'create table if not exists keywords('
                u'keyword varchar(100),'
                u'isbn varchar(100)'
                u');')
        finally:
            if not con:
                con.close()

    def search(self, keywords, page=1, index='All'):
        res = self._amazon.ItemSearch(
            Keywords=keywords,
            SearchIndex=index,
            ItemPage=str(page),
            ResponseGroup='Small')
        xml = res.decode('utf-8')
        return Result(xml)

    def addKeyword(self, user, status, keyword):
        logger.debug(u'%s added keyword "%s"', user, keyword)
        con = None
        try:
            con = sqlite3.connect(self._db_file)
            rows = list(con.execute(u'select * from user_keywords where user_id=? and keyword=?;', (user, keyword)))
            if len(rows) != 0:
                return True
            result = self.searchNewBooks(keyword)
            if len(result) == 0:
                isbn = ''
            else:
                isbn = result[0]['isbn']
            con.execute(u'insert into user_keywords(user_id, status_id, keyword) values(?,?,?);', (user, str(status.id), keyword))
            con.execute(u'insert into keywords(keyword, isbn) values(?,?);', (keyword, isbn))
            con.commit()
        finally:
            if not con:
                con.close()

    def getKeywords(self, user):
        con = None
        try:
            con = sqlite3.connect(self._db_file)
            keywords = [t[0] for t in con.execute(u'select keyword from user_keywords where user_id=?;', user)]
        finally:
            if not con:
                con.close()
        return keywords

    _re_mention = re.compile(ur'@\w+')
    def hook(self, bot, status):
        text = self._re_mention.sub('', status.text)
        text = unicodedata.normalize('NFKC', text)
        text = text.lower()
        m = self._re_hook.search(text)
        if m:
            keyword = m.group('keyword').strip()
            index = Amazon.searchIndexDic.get(m.group('index') or 'すべて', 'All')
            logger.debug('Keyword: %s, SearchIndex: %s', keyword, index)
            tweet = Tweet(self.search(keyword, index=index), amazon=self._amazon)
            tweet.reply_to(bot, status)
            return True

        m = self._re_tellme.search(text)
        if m:
            user = str(status.author.id)
            keyword = m.group('keyword').strip()
            self.addKeyword(user, status, keyword)
            bot.reply_to(u'おｋ。「{0}」の新刊が出たらお知らせします。 [{1}]'.format(keyword, bot.get_timestamp()), status)
            return True

        if u'新刊' in text and (u'通知' in text or u'知らせ' in text):
            if u'一覧' in text:
                user = str(status.author.id)
                keywords = self.getKeywords(user)
                if keywords:
                    bot.reply_to(u'「{0}」の新刊が出たらお知らせします。 [{1}]'.format(u'」「'.join(keywords), bot.get_timestamp()), status)
                else:
                    bot.reply_to(u'新刊通知機能は無効です。「hogehogeの新刊出たら教えて」とリプライをください。 [{0}]'.format(bot.get_timestamp()), status)
            else:
                bot.reply_to(u'「hogehogeの新刊出たら教えて」とリプライをください。 [{0}]'.format(bot.get_timestamp()), status)
            return True

        return False

    def searchNewBooks(self, keywords):
        res = self._amazon.ItemSearch(
            Keywords=keywords,
            SearchIndex='Books',
            ItemPage='1',
            ResponseGroup='Small',
            Sort='daterank')
        xml = res.decode('utf-8')
        return Result(xml)

    def cron(self, bot):
        logger.debug(u'checking update of books...')
        con = None
        try:
            con = sqlite3.connect(self._db_file)
            for keyword, isbn in con.execute(u'select keyword, isbn from keywords;'):
                logger.debug(u'checking "%s"...', keyword)
                result = self.searchNewBooks(keyword)
                if len(result) == 0 or result[0]['isbn'] == isbn:
                    continue
                logger.debug(u'found new book: %s', result[0]['isbn'])
                for user_id, status_id in con.execute(u'select user_id, status_id from user_keywords where keyword=?', (keyword, )):
                    try:
                        user = bot.api.get_user(user_id)
                        status = bot.api.get_status(status_id)
                        tweet = Tweet(result, amazon=self._amazon)
                        tweet.reply_to(bot, status)
                    except:
                        pass
                con.execute(u'update keywords set isbn=? where keyword=?', (result[0]['isbn'], keyword))
                con.commit()
        finally:
            if not con:
                con.close()
