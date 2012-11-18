#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
マルコフ連鎖による文章作成プログラム
"""

import sys
import codecs
import random

from dbmanager import DBManager

class MarkovGenerator(object):
    def __init__(self, db):
        self.db = db
        self.random = random.Random()

    def get_text(self, reply_to = None):
        db = self.db
        text = ''
        word = db.BOS
        distribution = {}

        # 1-gramの出現頻度を計算しておく
        if reply_to:
            distribution = db.reply_word(reply_to)

        # 文章生成
        while True:
            next_word = self.get_next(word, distribution)
            if not next_word or next_word==db.EOS:
                break
            text += next_word.split('\t')[0]
            word = next_word
        return text

    def get_next(self, word, distribution = None):
        """wordの次の単語を決定する"""
        distribution = distribution or {}
        db = self.db
        word_list = []
        count_sum = 0
        for word, count in db.next_word(word):
            count_sum += count * (distribution.get(word, 0) + 1)
            word_list.append((word, count_sum))

        selection = self.random.random() * count_sum
        for word, count in word_list:
            if selection<count:
                return word
        
if __name__=="__main__":
    sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    db = DBManager()
    for i in xrange(100):
        print MarkovGenerator(db).get_text()
