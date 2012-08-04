# -*- coding:utf-8 -*-

import MeCab
import jcconv
import re

class Ondulish:
    def __init__(self, tagger=None):
        self._tagger = tagger or MeCab.Tagger()
        self._ondulish = MeCab.Tagger('-d dic/ondulish')

    def _yomi(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        node = self._tagger.parseToNode(text)
        yomi = ''
        while node:
            if node.stat>=2:
                node = node.next
                continue
            if node.stat==0:
                features = node.feature.split(',')
                yomi += features[7]
            else:
                yomi += node.surface

            node = node.next
        return jcconv.hira2kata(yomi.decode('utf-8'))

    def translate(self, text):
        yomi = self._yomi(text).encode('utf-8')
        yomi = self._ondulish.parse(yomi)
        return jcconv.kata2half(yomi.decode('utf-8'))

    _re_ondulish = re.compile(u'[ｱ-ﾝﾞﾟ]{5,}')
    def detect(self, text):
        return not self._re_ondulish.search(text) is None

if __name__=='__main__':
    import sys
    t = Ondulish()
    print t.translate(' '.join(sys.argv[1:]))
