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
import busNUT
from Translator import Translator
import DayOfTheWeek
from wolframalpha import WolframAlpha

logger = logging.getLogger("BaseBot")

class GlobalCloneBot(CloneBot):
    def __init__(self, crawl_user, mecab=None, log_file='crawl.tsv', db_file='bigram.db'):
        super(GlobalCloneBot, self).__init__(crawl_user, mecab, log_file, db_file)
        self.translator = Translator(config.BING_APP_KEY, 'ja', 'en')

    def reply_hook(self, bot, status):
        """適当にリプライを返してあげる"""
        text = self.get_text()
        if status:
            bot.reply_to(text, status)
        else:
            bot.update_status(text)
            #時々英訳
            if random.random()<0.2:
                text = self.translator.translate(text)
                bot.update_status(u'[Translated] '+text)
                #時々再翻訳
                if random.random()<0.5:
                    text = self.translator.translate(text, 'en', 'ja')
                    bot.update_status(u'[再翻訳] ' + text)
        return True

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
                reply_limit = 2,
                reset_cycle = 20*60,
                allowed_users = config.BOT_USER))
        self.append_reply_hook(AdminFunctions.history_hook(
                reply_limit = config.REPLY_LIMIT,
                reset_cycle = config.RESET_CYCLE,
                limit_msg = u'今、ちょっと取り込んでまして・・・'
                              u'またのご利用をお待ちしております！'))
        self.append_reply_hook(JO_RI_bot.limit_hook)

        self.translator = Translator(config.BING_APP_KEY)
        self.append_reply_hook(self.translator.hook)

        dokusho = Dokusho(
            config.CRAWL_USER,
            config.DOKUSHO_USER,
            config.AMAZON_ACCESS_KEY_ID,
            config.AMAZON_SECRET_ACCESS_KEY)
        self.append_reply_hook(dokusho.hook)
        self.append_cron('0 0 * * mon', dokusho.crawl)

        self.append_reply_hook(gakushoku.GakuShoku(
                config.MENU_EMAIL, config.MENU_PASSWORD,
                config.MENU_ID, config.MENU_SHEET).hook)

        self.append_reply_hook(busNUT.Bus().hook)
        self.append_reply_hook(DayOfTheWeek.hook)
        self.append_reply_hook(JO_RI_bot.nullpo)

        self.wolfram = WolframAlpha(config.WOLFRAM_ALPHA_APP_ID, self.translator)
        self.append_reply_hook(self.wolfram.hook)

        self.clone_bot = GlobalCloneBot(config.CRAWL_USER)
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

    def nullpo(self, status):
        """ぬるぽ→ガッ"""
        if status.text.find(u'ぬるぽ')<0:
            return False
        bot.reply_to(u'ｶﾞｯ [%s]' % bot.get_timestamp(), status)
        return True


if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
