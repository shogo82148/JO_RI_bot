# -*- coding:utf-8 -*-

import urllib
import re

class Enteisla:
    def __init__(self):
        dic = {}
        for en, ei in zip(
            "abcdefghijklmnopqrstuvwxyz",
            "azyxewvtisrqpnomlkjhugfdcb"):
            dic[en] = ei
            dic[ei.upper()] = en.upper()
        self.dic = dic

    def translate(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        dic = self.dic
        res = ''.join(dic.get(ch, ch) for ch in text)
        return res

    def detect(self, text):
        return False

if __name__=='__main__':
    import sys
    t = Enteisla()
    print t.translate(' '.join(sys.argv[1:]))
