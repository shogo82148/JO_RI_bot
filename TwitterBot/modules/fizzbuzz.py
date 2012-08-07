# -*- coding:utf-8 -*-

import re
import unicodedata
import random

_re_mention = re.compile(ur'@\w+')
_re_number = re.compile(ur'[0-9]+')

def hook(bot, status):
    def fizzbuzz(num):
        if num % 15 == 0:
            return (-1, True, True)
        elif num % 5 == 0:
            return (-1, False, True)
        elif num % 3 == 0:
            return (-1, True, False)
        return (num, False, False)

    def makehook(num):
        def getuseranswer(text):
            text = unicodedata.normalize('NFKC', text)
            text = text.lower()
            text = _re_mention.sub('', text)

            number = -1
            m = _re_number.search(text)
            if m:
                number = int(m.group())
            fizz = text.find(u'fizz') >= 0
            buzz = text.find(u'buzz') >= 0
            return (number, fizz, buzz)

        def f(bot, status):
            useranswer = getuseranswer(status.text)
            if useranswer == fizzbuzz(num):
                n, fizz, buzz = fizzbuzz(num + 1)
                text = ''
                if n >= 0:
                    text += str(n) + ' '
                if fizz:
                    text += 'Fizz '
                if buzz:
                    text += 'Buzz '
                text += '[%s]' % bot.get_timestamp()
                new_status = bot.reply_to(text, status)
                bot.append_reply_hook(
                    makehook(num + 2),
                    name='fizzbuzz-%d' % new_status.id,
                    in_reply_to=new_status.id,
                    time_out=30*60)
            else:
                bot.reply_to(
                    u'm9(^Д^)[%s]' % bot.get_timestamp(),
                    status
                    )
            return True
        return f

    text = unicodedata.normalize('NFKC', status.text)
    text = text.lower()
    if text.find(u'fizz') < 0 and text.find(u'buzz') < 0:
        return False

    if random.random()<0.5:
        new_status = bot.reply_to(
            u'FizzBuzzはじめるよ！ 1 [%s]' % bot.get_timestamp(),
            status
            )
        bot.append_reply_hook(makehook(2), name='fizzbuzz-%d' % new_status.id, in_reply_to=new_status.id, time_out=30*60)
    else:
        new_status = bot.reply_to(
            u'FizzBuzzはじめるよ！ [%s]' % bot.get_timestamp(),
            status
            )
        bot.append_reply_hook(makehook(1), name='fizzbuzz-%d' % new_status.id, in_reply_to=new_status.id, time_out=30*60)
    return True

