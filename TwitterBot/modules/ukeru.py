# -*- coding: utf-8 -*-

# https://twitter.com/ayuha167/status/258020691755036672

import random

def hook(bot, status):
    text = status.text
    if text.find(u'マジ')<0 and text.find(u'ヤバ')<0 and text.find(u'ウケ')<0:
        return False

    def ukeru(bot, status):
        text = random.choice([u'マジで', u'ヤバい', u'ウケルー'])
        new_status = bot.reply_to(
            text + ' [{0}]'.format(bot.get_timestamp()),
            status)
        bot.append_reply_hook(
            ukeru,
            name='ukeru-%d' % new_status.id,
            in_reply_to=new_status.id,
            time_out=60*60)
        return True

    return ukeru(bot, status)
