#!/usr/bin/env python
# -*- coding:utf-8 -*-

import config
import BaseBot
import datetime
import random
import logging

logger = logging.getLogger("BaseBot")

class JO_RI_bot(BaseBot.BaseBot):
    def __init__(self):
        super(JO_RI_bot, self).__init__(config.CONSUMER_KEY,
                                        config.CONSUMER_SECRET,
                                        config.ACCESS_KEY,
                                        config.ACCESS_SECRET)
        self.ignore_user = [name.lower() for name in config.IGNORE_USER]
        self.admin_user = [name.lower() for name in config.ADMIN_USER]
        self.reply_history = {}
        self.append_reply_hook(JO_RI_bot.shutdown_hook)
        self.append_reply_hook(JO_RI_bot.delete_hook)

    def on_start(self):
        self.update_status(random.choice([
                    u'【お知らせ】颯爽登場、銀河美少年！ 綺羅星☆[%s]',
                    u'【お知らせ】ほろーん',
                    u'【お知らせ】起動なう[%s]',
                    ]) % str(datetime.datetime.now()))

    def on_shutdown(self):
        self.update_status(random.choice([
                    u'【お知らせ】目がぁぁぁ、目がぁぁぁぁ[%s]',
                    u'【お知らせ】ボットは滅びぬ、何度でも蘇るさ[%s]',
                    u'【お知らせ】シャットダウンなう[%s]',
                    ]) % self.get_timestamp())

    def delete_hook(self, status):
        """削除コマンド"""
        if status.text.find(u'削除')<0:
            return False
        if status.author.screen_name.lower() in self.admin_user:
            #削除実行
            if status.in_reply_to_status_id:
                self.destroy_status(status.in_reply_to_status_id)
            else:
                self.reply_to(u'in_reply_to入ってないよ！[%s]' % self.get_timestamp())
            return True
        return False

    def shutdown_hook(self, status):
        """シャットダウンコマンド"""
        if status.text.find(u'バルス')<0:
            return False
        if status.author.screen_name.lower() in self.admin_user:
            raise BaseBot.BotShutdown
        else:
            return False

if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
