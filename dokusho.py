#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
読書メータクロールプログラム
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
import config
import anydbm
import itertools
import logging

logger = logging.getLogger("BaseBot")

_dokusho_base = 'http://book.akahoshitakuya.com'

class Dokusho(object):
    def __init__(self, user_name, user, access_key, secret_key, db_file='dokusho.db'):
        self._user = user
        self._user_name = user_name
        self._amazon = bottlenose.Amazon(
            access_key, secret_key, Region='JP')
        self._associate_tag = config.AMAZON_ASSOCIATE_TAG
        self._db_file = db_file

    def commentlist(self, page=1):
        """コメントをクロールする"""
        url = '%s/u/%s/commentlist&p=%d' % (_dokusho_base, self._user, page)
        html = urllib2.urlopen(url).read().decode('utf-8')
        root = lxml.html.fromstring(html)
        log_list = root.xpath('//div[@class="log_list_detail"]')

        for log in log_list:
            try:
                comment = log.xpath('./span/text()')[0]
                comment = comment.replace('\n',' ').replace('\t', ' ')
                book_link = log.xpath('./a[starts-with(@href,"/b/") and @title]')[0]
                isbn = book_link.attrib['href'].split('/')[-1]
                title = book_link.attrib['title']
                yield {
                    'comment': comment,
                    'isbn': isbn,
                    'title': title,
                    }
            except IndexError:
                pass
    
    def booklist(self, page=1):
        """読んだ本をクロールする"""
        url = '%s/u/%s/booklist&p=%d' % (_dokusho_base, self._user, page)
        html = urllib2.urlopen(url).read().decode('utf-8')
        root = lxml.html.fromstring(html)
        log_list = root.xpath('//div[@class="book"]')

        for log in log_list:
            
                book_link = log.xpath('./a[starts-with(@href,"/b/")]')[0]
                isbn = book_link.attrib['href'].split('/')[-1]
                title = log.xpath('./a[starts-with(@href,"/b/")]/img/@alt')[0]
                yield {
                    'comment': '',
                    'isbn': isbn,
                    'title': title,
                    }

    def _page_cursor(self, func):
        for page in itertools.count(1):
            items = list(func(page))
            if len(items)==0:
                break
            for item in items:
                yield item

    def crawl(self, bot=None):
        """読書メータのコメントをクロールする"""
        try:
            db = anydbm.open(self._db_file, 'c')

            #読んだ本のクロール
            for item in self._page_cursor(self.booklist):
                if item['isbn'] in db:
                    break
                logger.info('Read: ' + item['title'])
                db[item['isbn']] = ''

            #コメントのクロール
            for item in self._page_cursor(self.commentlist):
                if item['isbn'] in db and db[item['isbn']]:
                    break
                logger.info('Commented: ' + item['title'])
                db[item['isbn']] = item['comment'].encode('utf-8')

        finally:
            db.close()
    
    def search(self, keywords, page=1):
        res = self._amazon.ItemSearch(
            Keywords=keywords,
            SearchIndex='Books',
            ItemPage=str(page),
            ResponseGroup='Small',
            AssociateTag=self._associate_tag)
        xml = res.decode('utf-8')
        tree = lxml.etree.fromstring(xml)
        return tree

    def get_comment(self, keyword):
        namespaces={'ns':"http://webservices.amazon.com/AWSECommerceService/2011-08-01"}
        def toDict(db, item):
            isbn = item.xpath('.//ns:ASIN/text()', namespaces = namespaces)[0]
            item_dict = {}
            item_dict['isbn'] = isbn
            if isbn in db:
                item_dict['comment'] = db[isbn].decode('utf-8')
            else:
                item_dict['comment'] = None
            item_dict['title'] = item.xpath('.//ns:Title/text()', namespaces = namespaces)[0]
            item_dict['links'] = dict(zip(
                    item.xpath('.//ns:Description/text()', namespaces = namespaces),
                    item.xpath('.//ns:URL/text()', namespaces = namespaces),
                    ))
            return item_dict
            
        res = self.search(keyword)
        items = res.xpath('//ns:Item', namespaces = namespaces)
        try:
            db = anydbm.open(self._db_file, 'c')
            for item in items:
                isbn = item.xpath('.//ns:ASIN/text()', namespaces = namespaces)[0]
                if isbn in db:
                    return toDict(db, item)
            if len(items)>0:
                return toDict(db, items[0])
        finally:
            db.close()
        return None

    _re_mention = re.compile(ur'@\w+')
    _re_hook = re.compile(ur'^(.*)の(感想|かんそう|かんそー)を?(教えて|おしえて)')
    def hook(self, bot, status):
        text = self._re_mention.sub('', status.text)
        m = self._re_hook.search(text)
        if not m:
            return False

        keyword = m.group(1).strip()
        item = self.get_comment(keyword)
        if not item:
            bot.reply_to(
                u'「%s」という本は見つかりませんでした[%s]' % (keyword, bot.get_timestamp()), status)
        elif not item['comment']:
            if item['comment'] is None:
                text = u'%sは「%s」を未読です。買って読んでみては？' % (
                    self._user_name, item['title'])
            else:
                text = u'%sは「%s」を読んだけどコメントは未投稿です。買って読んでみては？' % (
                    self._user_name, item['title'])
            limit = 140 - len(text)
            limit -= len('@' + status.author.screen_name + ' ')
            if limit>=21:
                text += ' ' + item['links']['All Customer Reviews']
                limit -= 21
            if limit>=21:
                text += ' %s/b/%s' % (_dokusho_base, item['isbn'])
                limit -= 21
            timestamp = u' [%s]' % bot.get_timestamp()
            if limit>len(timestamp):
                text += timestamp
            bot.reply_to(text, status, cut=False)
        else:
            comment = item['comment']
            limit = 140
            limit -= 1 + 20 #For URL
            limit -= len('@' + status.author.screen_name + ' ')
            if len(comment)>limit:
                comment = comment[0:limit-1] + u'…'
            bot.reply_to(comment + ' %s/b/%s' % (_dokusho_base, item['isbn']), status, cut=False)
        return True

def main():
    import config

    dokusho = Dokusho(
        u'JO_RI',
        config.DOKUSHO_USER,
        config.AMAZON_ACCESS_KEY_ID,
        config.AMAZON_SECRET_ACCESS_KEY)

    query = ''
    if len(sys.argv)>1:
        query = sys.argv[1].decode('utf-8')
    for name, val in dokusho.get_comment(query).iteritems():
        print name, val

if __name__=="__main__":
    sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    main()

