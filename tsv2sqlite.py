#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import codecs

from dbmanager import DBManager
sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

def main():
    db = DBManager()
    for line in sys.stdin:
        status = line.split('\t')[0]
        db.add_text(status)
        print line
        sys.stdout.flush()
    return

if __name__=="__main__":
    main()
