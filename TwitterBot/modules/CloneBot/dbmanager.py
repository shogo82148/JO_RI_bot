#!/usr/bin/env python
# -*- coding:utf-8 -*-

import MeCab
import config
import anydbm
import re
import sys

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
    BOS = '\tBOS/EOS,*,*'
    EOS = '\tBOS/EOS,*,*'
    bigram_columns = ['count', 'following']

    def __init__(self, mecab=None, dbfile='bigram.db'):
        self._mecab = mecab or MeCab.Tagger()
        self.db = anydbm.open(dbfile, 'c')
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def close(self):
        if not self._closed:
            self.db.close()
            self._closed = True

    _re_mention = re.compile(r'@\w+')
    _re_url = re.compile(r'(http)://[_\.a-zA-Z0-9\?&=\-%/#!]*')
    _re_hash_tag = re.compile(ur'#[\w\u3041-\u3094\u30a1-\u30fa\u30fc'
                   ur'\u4e00-\u9fff\uf900-\ufaff]+')
    _re_retweet = re.compile(r'(RT|QT) @\w+:.*$')
    _re_space = re.compile(r'\s+')
    _re_dot = re.compile(r'^\.\s*')
    def extract_text(self, text):
        """URLやメンションなどを削除する"""
        if self._re_url.search(text):
            return ''
        text = self._re_hash_tag.sub('', text)
        text = self._re_retweet.sub('', text)
        text = self._re_mention.sub('', text)
        text = self._re_dot.sub('', text)
        text = self._re_space.sub(' ', text)
        text = text.strip()
        return text

    def node2word(self, node):
        features = node.feature.split(',')[0:3]
        text = "%s\t%s,%s,%s" % tuple([node.surface]+features)
        return text.decode('utf-8')

    def add_text(self, text):
        """ テキストをデータベースに登録する """

        db = self.db
        bigrams = {}
        nodes = Parse(text, self._mecab)
        g = (self.node2word(n) for n in nodes)

        for word1, word2 in Bigram(g):
            w1 = word1.encode('utf-8')
            w2 = word2.encode('utf-8')
            bigram = w1 + '\n' + w2

            if bigram not in db:
                db[bigram] = '1'
                if w1 not in db:
                    db[w1] = w2
                else:
                    db[w1] += '\n' + w2
            else:
                db[bigram] = str(int(db[bigram])+1)

    def next_word(self, word):
        """ wordの次に出現する単語を探す """
        db = self.db
        str_word = word.encode('utf-8')
        if str_word in db:
            next_words = db[str_word].split('\n')
            for w in next_words:
                key = str_word+'\n'+w
                if key not in db:
                    continue
                yield (w.decode('utf-8'), int(db[key]))

    def _get_since_id(self):
        if 'since_id' in self.db:
            return self.db['since_id']
        else:
            return ''

    def _set_since_id(self, since_id):
        self.db['since_id'] = str(since_id)

    since_id = property(_get_since_id, _set_since_id)


if __name__=="__main__":
    db = DBManager()
    query = " ".join(sys.argv[1:])
    print query
    for res in db.db.execute(query):
        print '\t'.join(unicode(i) for i in res)
