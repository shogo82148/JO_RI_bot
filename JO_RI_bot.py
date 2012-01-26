#!/usr/bin/env python
# -*- coding:utf-8 -*-

import config
import BaseBot
import AdminFunctions
import datetime
import random
import logging
import gakushoku

logger = logging.getLogger("BaseBot")

class JO_RI_bot(BaseBot.BaseBot):
    def __init__(self):
        super(JO_RI_bot, self).__init__(config.CONSUMER_KEY,
                                        config.CONSUMER_SECRET,
                                        config.ACCESS_KEY,
                                        config.ACCESS_SECRET)
        self.append_reply_hook(AdminFunctions.shutdown_hook(
                allowed_users = config.ADMIN_USER,
                command = u'バルス'))
        self.append_reply_hook(AdminFunctions.delete_hook(
                allowed_users = config.ADMIN_USER,
                command = u'削除',
                no_in_reply = u'in_reply_to入ってないよ！'))
        self.append_reply_hook(gakushoku.GakuShoku().hook)

    def on_start(self):
        self.update_status(random.choice([
                    u'【お知らせ】颯爽登場、銀河美少年！ 綺羅星☆[%s]',
                    u'【お知らせ】ほろーん[%s]',
                    u'【お知らせ】起動なう[%s]',
                    ]) % self.get_timestamp())

    def on_shutdown(self):
        self.update_status(random.choice([
                    u'【お知らせ】目がぁぁぁ、目がぁぁぁぁ[%s]',
                    u'【お知らせ】ボットは滅びぬ、何度でも蘇るさ[%s]',
                    u'【お知らせ】シャットダウンなう[%s]',
                    ]) % self.get_timestamp())

if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
