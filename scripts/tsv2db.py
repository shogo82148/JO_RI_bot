#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import codecs

from TwitterBot.modules.CloneBot.dbmanager import DBManager
sys.stdin  = codecs.getreader('utf-8')(sys.stdin)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

def main():
    db = DBManager()
    for line in sys.stdin:
        line = line.strip()
        status = line.split('\t')
        if len(status) < 2:
            continue
        text = db.extract_text(status[0])
        reply = None
        if len(status) >= 4:
            reply = db.extract_text(status[3])
        if text:
            db.add_text(text, reply)
            print text, '\t', status[1]
        if len(status)>=3:
            db.since_id = status[2]
        sys.stdout.flush()
    return

if __name__=="__main__":
    main()
