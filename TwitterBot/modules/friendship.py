# -*- coding:utf-8 -*-

import TwitterBot

def breaker(bot, status):
    def ignore(bot, s):
        return s.author.id == status.author.id

    if status.text.find(u'絶交')>=0:
        if bot.api.exists_friendship(bot.api.me().id, status.author.id):
            bot.reply_to(u'アンフォローしました。またのご利用をお待ちしています。 [%s]' % bot.get_timestamp(), status)
            bot.api.destroy_friendship(status.author.id)
        else:
            bot.reply_to(u'お前となんか！絶交だ！ [%s]' % bot.get_timestamp(), status)
            bot.append_reply_hook(
                ignore,
                name='destroy-friendship-' + status.author.screen_name,
                time_out=60*60,
                priority=TwitterBot.PRIORITY_ADMIN)
        return True

    if status.text.find(u'アンフォロ')>=0:
        if bot.api.exists_friendship(bot.api.me().id, status.author.id):
            bot.reply_to(u'アンフォローしました。またのご利用をお待ちしています。 [%s]' % bot.get_timestamp(), status)
            bot.api.destroy_friendship(status.author.id)
        else:
            return False
        return True

    return False
