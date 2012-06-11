# -*- coding: utf-8 -*-

# (」・ω・)」うー！(／・ω・)／にゃー！
import re
import unicodedata

u = u"(」・ω・)」うー！"
nya = u"(／・ω・)／にゃー！"
letsnya = u"Let's＼(・ω・)／にゃー！"

class Unya(object):
    def __init__(self, count = 0):
        self.count = count

    def hook(self, bot, status):
        text = unicodedata.normalize('NFKC', status.text)
        has_u = text.find(u'(」・ω・)」う')>0
        has_nya = text.find(u'(/・ω・)/にゃ')>0
        has_unya = text.find(u'うーにゃー')>0 or (has_u and has_nya)

        new_unya = None
        res = None
        if has_unya:
            new_unya = Unya(self.count + 2)
            if new_unya.count % 4 == 0:
                res = letsnya
            elif new_unya.count % 4 == 3:
                res = u + nya + letsnya
                new_unya.count += 1
            else:
                res = u + nya
        elif has_u:
            new_unya = Unya(self.count + 1)
            if new_unya.count % 4 == 3:
                res = nya + letsnya
                new_unya.count += 1
            else:
                res = nya

        if new_unya and res:
            new_status = bot.reply_to(u'%s [%s]' % (res, bot.get_timestamp()), status)
            bot.append_reply_hook(new_unya.hook, name='unya-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)
            return True
