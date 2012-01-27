#!/usr/bin/env python
# -*- coding:utf-8 -*-

import config
import BaseBot
import AdminFunctions
import datetime
import random
import logging
import gakushoku
from CloneBot import CloneBot
from dokusho import Dokusho
logger = logging.getLogger("BaseBot")

class JO_RI_bot(BaseBot.BaseBot):
    def __init__(self):
        super(JO_RI_bot, self).__init__(config.CONSUMER_KEY,
                                        config.CONSUMER_SECRET,
                                        config.ACCESS_KEY,
                                        config.ACCESS_SECRET)
        self.append_reply_hook(AdminFunctions.shutdown_hook(
                allowed_users = config.ADMIN_USER,
                command = set([u'バルス', u'シャットダウン', u'shutdown', u'halt', u':q!', u'c-x c-c'])))
        self.append_reply_hook(AdminFunctions.delete_hook(
                allowed_users = config.ADMIN_USER,
                command = set([u'削除', u'デリート', u'delete']),
                no_in_reply = u'in_reply_to入ってないよ！'))
        self.append_reply_hook(AdminFunctions.history_hook(
                reply_limit = config.REPLY_LIMIT,
                reset_cycle = config.RESET_CYCLE,
                limit_msg = u'今、ちょっと取り込んでまして・・・'
                              u'またのご利用をお待ちしております！'))
        self.append_reply_hook(JO_RI_bot.limit_hook)

        dokusho = Dokusho(
            config.CRAWL_USER,
            config.DOKUSHO_USER,
            config.AMAZON_ACCESS_KEY_ID,
            config.AMAZON_SECRET_ACCESS_KEY)
        self.append_reply_hook(dokusho.hook)

        self.append_reply_hook(gakushoku.GakuShoku(
                config.MENU_EMAIL, config.MENU_PASSWORD,
                config.MENU_ID, config.MENU_SHEET).hook)

        self.clone_bot = CloneBot(config.CRAWL_USER)
        self.append_reply_hook(self.clone_bot.reply_hook)
        self.append_cron('30 * * * *',
                         self.clone_bot.crawl,
                         name=u'Cron Crawling')
        self.append_cron('*/20 * * * *',
                         self.clone_bot.update_status,
                         name=u'Cron Update Status')

    def on_start(self):
        self.clone_bot.crawl(self)
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

    def limit_hook(self, status):
        text = status.text.lower()
        if text.find(u'api')<0:
            return False
        if text.find(u'残')<0:
            return False
        if text.find(u'報告')<0 and text.find(u'教')<0 and text.find(u'レポート')<0:
            return False
        limit = self.api.rate_limit_status()
        self.reply_to(u'API残数: %(remaining_hits)d/%(hourly_limit)d,'
                      u'リセット予定:%(reset_time)s (' % limit + self.get_timestamp()+')',
                      status)
        return True

if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
