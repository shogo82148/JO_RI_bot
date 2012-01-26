#!/usr/bin/env python
# -*- coding:utf-8 -*-

import BaseBot
import datetime
import logging

class admin_hook(object):
    """特定ユーザしか実行できないコマンド"""
    def __init__(self, allowed_users=None):
        self._allowed_users = None
        if allowed_users:
            self._allowed_users = set([name.lower() for name in allowed_users])

    def is_allowed(self, status):
        """実行可能か判定"""
        if not self._allowed_users:
            return True
        if isinstance(status, (unicode, str)):
            return status.lower() in self._allowed_users
        else:
            return status.author.screen_name.lower() in self._allowed_users

    def __call__(self, bot, status):
        pass

class delete_hook(admin_hook):
    """削除コマンド"""
    def __init__(self, allowed_users=[], command=None, no_in_reply=None, not_allowed=None):
        super(delete_hook, self).__init__(allowed_users)
        self._command = command
        self._no_in_reply = no_in_reply
        self._not_allowed = not_allowed

    def __call__(self, bot, status):
        if not self._command or status.text.find(self._command)<0:
            return False
        if self.is_allowed(status):
            if status.in_reply_to_status_id:
                self.destroy_status(status.in_reply_to_status_id)
            elif self._no_in_reply:
                self.reply_to(u'%s [%s]' % 
                              (self._no_in_reply, bot.get_timestamp()) )
            return True

        if self._not_allowed:
            self.reply_to(u'%s [%s]' % 
                          (self._not_allowed, bot.get_timestamp()) )
        return False
                              
class shutdown_hook(admin_hook):
    """シャットダウンコマンド"""
    def __init__(self, allowed_users=[], command=None, no_in_reply=None):
        super(shutdown_hook, self).__init__(allowed_users)
        self._command = command
        self._no_in_reply = no_in_reply

    def __call__(self, bot, status):
        if not self._command or status.text.find(self._command)<0:
            return False
        if self.is_allowed(status):
            raise BaseBot.BotShutdown
        return False

