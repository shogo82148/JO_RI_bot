#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
特定ユーザのつぶやきを真似するボットさん
"""

from igo.Tagger import Tagger
import logging
import tweepy
from dbmanager import DBManager
from generator import MarkovGenerator

logger = logging.getLogger("Bot.Clone")

class CloneBot(object):
    def __init__(self, crawl_user, mecab=None, log_file='crawl.tsv', db_file='bigram.db', crawler_api=None):
        self._crawl_user = crawl_user
        self._mecab = mecab or Tagger('ipadic')
        self._log_file = log_file
        self._db_file = db_file
        self._crawler_api = crawler_api

    def reply_hook(self, bot, status):
        """適当にリプライを返してあげる"""
        if status:
            text = self.get_text(status.text)
            bot.reply_to(text, status)
        else:
            text = self.get_text()
            bot.update_status(text)
        return True

    def update_status(self, bot):
        self.reply_hook(bot, None)

    def get_text(self, reply_to = None):
        with DBManager(self._mecab, self._db_file) as db:
            text = MarkovGenerator(db).get_text(reply_to)
        return text

    def crawl(self, bot):
        """オリジナルユーザの発言をクロール"""
        def remove_tab(text):
            return text.replace('\t', ' ').replace('\n', ' ')

        with DBManager(self._mecab, self._db_file) as db:
            api = self._crawler_api or bot.api
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
                reply_text = db.extract_text(reply_to.text) if reply_to else None
                logger.debug('%s: %s' % (status.id, status.text))
                if reply_to:
                    logger.debug('>%s: %s' % (reply_to.id, reply_to.text))
                db.add_text(text, reply_text)
                db.since_id = str( max(int(db.since_id or 0), int(status.id)) )
                
        with open(self._log_file, 'a') as f:
            for line in reversed(new_statuses):
                f.write(line.encode('utf-8')+'\n')
