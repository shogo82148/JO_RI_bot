#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib
import urllib2
import datetime
import re
import json

_search_event_arg = frozenset([
        'event_id', 'keyword', 'keyword_or',
        'ym', 'ymd', 'user_id', 'nickname',
        'twitter_id', 'owner_id', 'owner_nickname',
        'owner_twitter_id', 'start', 'count', 'format',
        ])

def _tostr(value, date_format=''):
    if isinstance(value, (list, tuple)):
        return ','.join(_tostr(value, date_format))
    elif isinstance(value, unicode):
        return  value.encode('utf-8')
    elif isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime(date_format)
    else:
        return str(value)    

def search_events(**kargs):
    api_url = 'http://api.atnd.org/events/'
    params = {}
    for name, value in kargs.iteritems():
        if name not in _search_event_arg:
            raise Exception('Not Allowed Arg:'+name)
        date_format = ''
        if name=='ym':
            date_format = '%Y%m'
        elif name=='ymd':
            date_format = '%Y%m%d'
        params[name] = _tostr(value, date_format)
    url = api_url + '?' + urllib.urlencode(params)
    return urllib2.urlopen(url).read()

class SearchResult(object):
    def __init__(self, result, no=0):
        self.result = result
        self.no = no

    def update_status(self, bot, status):
        no = self.no
        if no>=len(self.result['events']):
            bot.reply_to(u'もうないよ [%s]' % bot.get_timestamp(), status)
            return
        event = self.result['events'][no]
        limit = 140
        limit -= 21 #for URL
        timestamp = ' [%s]' % bot.get_timestamp()
        limit -= len(timestamp)

        text = u'@%s %s' % (status.author.screen_name, event['title'])
        if len(text)>=limit:
            text = text[0:limit]
        limit -= len(text)

        if limit>=12:
            limit -= 2
            catch = event['catch']
            if len(catch)>limit:
                catch = catch[0:limit-1]+u'…'
            text += u'「%s」' % catch

        text += ' ' + event['event_url'] + timestamp
        new_status = bot.update_status(text,
                           in_reply_to_status_id=status.id)

        bot.append_reply_hook(self.hook, name='atnd-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)

    re_tag = re.compile(u'<.*?>')
    def update_detail(self, bot, status):
        no = self.no
        event = self.result['events'][no]
        limit = 140
        timestamp = ' [%s]' % bot.get_timestamp()
        limit -= len(timestamp)

        text = '@%s %s' % (status.author.screen_name, event['description'])
        text = self.re_tag.sub('', text)
        if len(text)>limit:
            text = text[0:limit]
        new_status = bot.update_status(text+timestamp, in_reply_to_status_id=status.id)
        bot.append_reply_hook(self.hook, name='atnd-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)

    re_other = re.compile(u'ほか|他|違う|ちがう|別|べつ')
    re_detail = re.compile(u'kwsk|詳|くわしく|(何|なに|ナニ)(それ|ソレ)')
    def hook(self, bot, status):
        if self.no>=len(self.result['events']):
            return

        m = self.re_other.search(status.text)
        if m:
            r = SearchResult(self.result, self.no+1)
            r.update_status(bot, status)
            return True

        m = self.re_detail.search(status.text)
        if m:
            self.update_detail(bot, status)
            return True

        return

_keyword_search = re.compile(ur'^@\w+\s+(.*?)[のな]?イベントを?教えて')
def keyword_search_hook(bot, status):
    m = _keyword_search.search(status.text)
    if not m:
        return
    keyword = m.group(1)
    result = json.loads(search_events(keyword=keyword, count=100, format='json'))
    if result['results_returned']==0:
        bot.reply_to(u'そんなものはなかった [%s]' % bot.get_timestamp(), status)
    else:
        r = SearchResult(result)
        r.update_status(bot, status)
    return True

_user_search = re.compile(ur'^@\w+\s+(.+?)が?参加(する|の)?イベントを?教えて')
def user_search_hook(bot, status):
    m = _user_search.search(status.text)
    if not m:
        return
    user = m.group(1)
    if user[0]=='@':
        result = json.loads(search_events(twitter_id=user[1:], count=100, format='json'))
    else:
        result = json.loads(search_events(nickname=user, count=100, format='json'))

    if result['results_returned']==0:
        bot.reply_to(u'そんなものはなかった [%s]' % bot.get_timestamp(), status)
    else:
        r = SearchResult(result)
        r.update_status(bot, status)
    return True

_owner_search = re.compile(ur'^@\w+\s+(.+?)が?主催者?(する|の)?イベントを?教えて')
def owner_search_hook(bot, status):
    m = _owner_search.search(status.text)
    if not m:
        return
    user = m.group(1)
    if user[0]=='@':
        result = json.loads(search_events(owner_twitter_id=user[1:], count=100, format='json'))
    else:
        result = json.loads(search_events(owner_nickname=user, count=100, format='json'))

    if result['results_returned']==0:
        bot.reply_to(u'そんなものはなかった [%s]' % bot.get_timestamp(), status)
    else:
        r = SearchResult(result)
        r.update_status(bot, status)
    return True

def hook(bot, status):
    if status.text.find(u'イベント教えて')<0 and status.text.find(u'イベントを教えて')<0:
        return
    if user_search_hook(bot, status):
        return True
    if owner_search_hook(bot, status):
        return True
    if keyword_search_hook(bot, status):
        return True

def main():
    print search_events(ym = datetime.datetime.today(), format='json')
    print search_events(twitter_id='shogo82148', format='json')

if __name__=='__main__':
    main()
