#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
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
import DateTimeHooks
import tweepy
import atnd

logger = logging.getLogger("Bot.JO_RI")

class GlobalCloneBot(CloneBot):
    def __init__(self, crawl_user, mecab=None, log_file='crawl.tsv', db_file='bigram.db', crawler_api=None):
        super(GlobalCloneBot, self).__init__(crawl_user, mecab, log_file, db_file, crawler_api)
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
                command = set([u'バルス', u'シャットダウン', u'shutdown', u'halt', u':q!', u'c-x c-c'])),
            priority=BaseBot.PRIORITY_ADMIN)
        self.append_reply_hook(AdminFunctions.delete_hook(
                allowed_users = config.ADMIN_USER,
                command = set([u'削除', u'デリート', u'delete']),
                no_in_reply = u'in_reply_to入ってないよ！'),
            priority=BaseBot.PRIORITY_ADMIN)
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

        self._gakushoku = gakushoku.GakuShoku(
                config.MENU_EMAIL, config.MENU_PASSWORD,
                config.MENU_ID, config.MENU_SHEET)
        self.append_reply_hook(self._gakushoku.hook)
        self.append_cron('00 11 * * *',
                         self._gakushoku.tweet_menu,
                         name = u'Gakushoku Menu(noon)',
                         args = (False,))
        self.append_cron('00 16 * * *',
                         self._gakushoku.tweet_menu,
                         name = u'Gakushoku Menu(afternoon)',
                         args = (True,))

        self.append_reply_hook(busNUT.Bus().hook)
        self.append_reply_hook(DayOfTheWeek.hook)
        self.append_reply_hook(DateTimeHooks.hook)
        self.append_reply_hook(atnd.hook)

        self.wolfram = WolframAlpha(config.WOLFRAM_ALPHA_APP_ID, self.translator)
        self.append_reply_hook(self.wolfram.hook)

        self.append_reply_hook(JO_RI_bot.typical_response)

        crawler_auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        crawler_auth.set_access_token(config.CRAWLER_ACCESS_KEY, config.CRAWLER_ACCESS_SECRET)
        crawler_api = tweepy.API(crawler_auth, retry_count=10, retry_delay=1)
        self.clone_bot = GlobalCloneBot(config.CRAWL_USER, crawler_api = crawler_api)
        self.append_reply_hook(self.clone_bot.reply_hook)
        self.append_cron('30 */2 * * *',
                         self.clone_bot.crawl,
                         name=u'Cron Crawling')
        self.append_cron('00 7-23 * * *',
                         self.clone_bot.update_status,
                         name=u'Cron Update Status')

    def on_start(self):
        self.clone_bot.crawl(self)
        self.update_status(random.choice([
                    u'【お知らせ】アプリボワゼ！颯爽登場！銀河美少年タウバーン！ [%s]',
                    u'【お知らせ】（<ゝω・）綺羅星☆[%s]',
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

    def typical_response(self, status):
        """決まりきった応答"""

        #ぬるぽ→ｶﾞｯ
        if status.text.find(u'ぬるぽ')>=0:
            bot.reply_to(u'ｶﾞｯ [%s]' % bot.get_timestamp(), status)
            return True

        #アプリボワゼ
        if status.text.find(u'アプリボワゼ')>=0:
            bot.reply_to(u'颯爽登場！！銀河美少年タウバーン！ [%s]' % bot.get_timestamp(), status)
            return True
        
        #颯爽登場！
        if status.text.find(u'颯爽登場')>=0:
            bot.reply_to(u'銀河美少年！タウバーン！ [%s]' % bot.get_timestamp(), status)
            return True

        #綺羅星→綺羅星
        if status.text.find(u'綺羅星')>=0:
            bot.reply_to(u'（<ゝω・）綺羅星☆ [%s]' % bot.get_timestamp(), status)
            return True
        
        #生存！→戦略！
        if status.text.find(u'生存')>=0 or status.text.find(u'せいぞん')>=0:
            if status.text.find(u'戦略')>=0 or status.text.find(u'せんりゃく')>=0:
                bot.reply_to(u'生存戦略、しましょうか [%s]' % bot.get_timestamp(), status)
            else:
                bot.reply_to(u'せんりゃくうううう！！！ [%s]' % bot.get_timestamp(), status)
            return True
        
        return False

    def is_spam(self, user):
        return user.screen_name=='JO_RI' or \
            user.statuses_count==0 or \
            user.followers_count*5<user.friends_count

    def on_follow(self, target, source):
        if source.screen_name==self._name:
            return
        if not source.protected and self.is_spam(source):
            text = u'@%s あなたは本当に人間ですか？JO_RI_botはボットからのフォローを受け付けておりません。' \
                u'人間だというなら1時間以内にこのツイートへ「ボットじゃないよ！」と返してもらえますか？ [%s]' \
                % (source.screen_name, self.get_timestamp())
            new_status = self.update_status(text)
            name = u'AreYouBot-%d' % new_status.id
            
            def hook(bot, status):
                if status.author.id!=source.id:
                    return
                if status.text.find(u'ボットじゃない')<0:
                    return
                self.reply_to(u'ボットじゃない・・・だと・・・ [%s]' % bot.get_timestamp(), status)
                self.delete_reply_hook(name)
                return True

            def timeout(bot):
                self.api.create_block(id=source.id)
                self.update_status(u'%sがスパムっぽいのでブロックしました [%s]'
                                   % (source.screen_name, self.get_timestamp()))

            self.append_reply_hook(hook, name=name,
                                   in_reply_to=new_status.id, time_out=60*60, on_time_out=timeout)
        else:
            text = u'@%s フォローありがとう！JO_RI_botは超高性能なボットです。' \
                u'説明書を読んでリプライを送ってみて！ ' \
                u'https://github.com/shogo82148/JO_RI_bot/wiki [%s]' \
                % (source.screen_name, self.get_timestamp())
            self.update_status(text)

            if source.protected:
                source.follow()

    re_follow_message = re.compile(ur'@(\w+)\s+フォローありがとう！')
    def on_favorite(self, target, source):
        m = self.re_follow_message.search(target.text)
        if not m:
            return
        if m.group(1)!=source.screen_name:
            return
        #self.api.create_friendship(source.id)

if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
