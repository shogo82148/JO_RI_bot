# -*- coding:utf-8 -*-

# 連想検索エンジン reflexa(http://labs.preferred.jp/reflexa/)
# へのアクセス

import re
import json
import urllib
import urllib2

re_search = re.compile(ur'^(.*)といえば[?？]?\s*$')
re_mention = re.compile(ur'@\w+')

def search(q):
    if isinstance(q, unicode):
        q = q.encode('utf-8')

    param = {
        'q': q,
        'format': 'json',
        }
    url = 'http://labs.preferred.jp/reflexa/api.php?' + urllib.urlencode(param)
    res = urllib2.urlopen(url)
    return json.load(res)

def hook(bot, status):
    text = re_mention.sub('', status.text).strip()

    m = re_search.search(text)
    if m:
        q = m.group(1)
        ans = search(q)
        if len(ans)==0:
            bot.reply_to(u'知らね [%s]' % bot.get_timestamp(), status)
            return True
        head = u'@%s ' % status.author.screen_name
        tail = u' [%s]' % bot.get_timestamp()
        msg = u''
        limit = 140 - len(head) - len(tail)
        limit -= 20
        tail = 'http://labs.preferred.jp/reflexa/search.php?' + urllib.urlencode({'q': q.encode('utf-8')}) + tail
        for s in ans:
            if limit - len(s) <= 0:
                break
            msg += s + u' '
            limit -= len(s) + 1
        bot.update_status(head + msg + tail, in_reply_to_status_id=status.id)
        return True
