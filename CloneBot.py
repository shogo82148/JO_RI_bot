#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
特定ユーザのつぶやきを真似するボットさん
"""

import MeCab
import logging
import tweepy
from dbmanager import DBManager
from generator import MarkovGenerator

logger = logging.getLogger("BaseBot")

class CloneBot(object):
    def __init__(self, crawl_user, mecab=None, log_file='crawl.tsv', db_file='bigram.db'):
        self._crawl_user = crawl_user
        self._mecab = mecab or MeCab.Tagger()
        self._log_file = log_file
        self._db_file = db_file

    def reply_hook(self, bot, status):
        """適当にリプライを返してあげる"""
        text = self.get_text()
        if status:
            bot.reply_to(text, status)
        else:
            bot.update_status(text)
        return True

    def update_status(self, bot):
        self.reply_hook(bot, None)

    def get_text(self):
        with DBManager(self._mecab, self._db_file) as db:
            text = MarkovGenerator(db).get_text()
        return text

    def crawl(self, bot):
        """オリジナルユーザの発言をクロール"""
        def remove_tab(text):
            return text.replace('\t', ' ').replace('\n', ' ')

        with DBManager(self._mecab, self._db_file) as db:
            api = bot.api
            arg = {}
            arg['id'] = self._crawl_user
            if db.since_id:
                arg['since_id'] = db.since_id

            new_statuses = []
            statuses = tweepy.Cursor(api.user_timeline, **arg).items(3200)
            for status in statuses:
                #テキストログを作成
                columns = [remove_tab(status.text), str(status.created_at), str(status.id)]

                #リプライ先も取得
                reply_to = None
                if status.in_reply_to_status_id:
                    try:
                        reply_to = api.get_status(status.in_reply_to_status_id)
                    except:
                        pass
                if reply_to:
                    columns.append(remove_tab(reply_to.text))
                    columns.append(str(reply_to.created_at))
                    columns.append(str(reply_to.id))
                    new_statuses.append('\t'.join(columns))

                #DBへ登録
                text = db.extract_text(status.text)
                logger.debug('%s: %s' % (status.id, status.text))
                if reply_to:
                    logger.debug('>%s: %s' % (reply_to.id, reply_to.text))
                db.add_text(text)
                db.since_id = str( max(int(db.since_id), int(status.id)) )
                
            with open('crawl.tsv', 'a') as f:
                for line in reversed(new_statuses):
                    f.write(line.encode('utf-8')+'\n')
