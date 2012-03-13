# -*- coding:utf-8 -*-

import MeCab

class Lou:
    def __init__(self):
        self._lou = MeCab.Tagger('-d dic/lou')

    def translate(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        text = self._lou.parse(text)
        return text.decode('utf-8')

if __name__=='__main__':
    import sys
    t = Lou()
    print t.translate(' '.join(sys.argv[1:]))
