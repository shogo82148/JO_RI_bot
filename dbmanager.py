#!/usr/bin/env python
# -*- coding:utf-8 -*-

import MeCab
import config
import sqlite3

class Parse:
    def __init__(self, s, tagger=None):
        tagger = tagger or MeCab.Tagger()
        self._node = None
        self._tagger = tagger
        self._s = s
        
    def next(self):
        if not self._node:
            self._node = self._tagger.parseToNode(self._s.encode('utf-8'))
            return self._node
        self._node = self._node.next
        if not self._node:
            raise StopIteration
        return self._node
        
    def __iter__(self):
        return self

def Bigram(itr):
    itr = iter(itr)
    a = next(itr)
    b = next(itr)
    while b:
        yield (a, b)
        a, b = b, next(itr)
        

class DBManager(object):
    bigram_columns = ['count', 'following']

    def __init__(self):
        self._mecab = MeCab.Tagger()

        self.db = sqlite3.connect("db.sqlite3")
        self.db.execute("create table if not exists bigram (word1 varchar(20),"
                        "word2 varchar(20),"
                        + ','.join('%s integer default 0' % column
                                   for column in self.bigram_columns) +
                        ");")
        self.db.commit()
        
    def add_text(self, text, column='count'):
        """ テキストをデータベースに登録する """

        if column not in self.bigram_columns:
            return

        bigrams = {}
        nodes = Parse(text, self._mecab)
        g = (("%s\t%s" % (n.surface, n.feature)).decode('utf-8') for n in nodes)

        for bigram in Bigram(g):
            bigrams[bigram] = bigrams.get(bigram, 0) + 1

        for bigram, count in bigrams.iteritems():
            dbbigram = self.db.execute(
                'select %s from bigram where word1=? and word2=?' % column, bigram).fetchone()
            if not dbbigram:
                self.db.execute(
                    'insert into bigram default values')
                self.db.execute(
                    'update bigram set word1=?, word2=? where word1 isnull and word2 isnull', bigram)
                dbbigram = (0,)
            self.db.execute(
                'update bigram set %s=? where word1=? and word2=?' % column,
                (dbbigram[0]+count, )+bigram)
        self.db.commit()

if __name__=="__main__":
    db = DBManager()
    db.add_text(u"こんにちは世界")
    db.add_text(u"こんにちはプログラム", column = 'following')
