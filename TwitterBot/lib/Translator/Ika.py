# -*- coding:utf-8 -*-

import urllib
import re

class Ika:
    def translate(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        url = 'http://ika.koneta.org/api?text=' + urllib.quote_plus(text)
        res = urllib.urlopen(url).read().decode('utf-8')
        return res

    _re_ika = re.compile(u'イカ|ゲソ')
    def detect(self, text):
        return not self._re_ika.search(text) is None

if __name__=='__main__':
    import sys
    t = Ika()
    print t.translate(' '.join(sys.argv[1:]))
