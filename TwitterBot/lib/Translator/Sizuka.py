# -*- coding:utf-8 -*-

import MeCab
import re

class Sizuka:
    def __init__(self, tagger=None):
        self._tagger = tagger or MeCab.Tagger()
        self._sizuka = MeCab.Tagger('-d dic/sizuka')
        self._antisizuka = MeCab.Tagger('-d dic/anti-sizuka')

    def translate(self, text):
        t = text.encode('utf-8')
        return self._sizuka.parse(t).decode('utf-8')

    def antitranslate(self, text):
        t = text.encode('utf-8')
        return self._antisizuka.parse(t).decode('utf-8')

    _re_sizuka = re.compile(u'♡')
    def detect(self, text):
        return not self._re_sizuka.search(text) is None

if __name__=='__main__':
    import sys
    t = Sizuka()
    a = t.translate(' '.join(sys.argv[1:]).decode('utf-8'))
    b = t.antitranslate(a)
    print a
    print b
