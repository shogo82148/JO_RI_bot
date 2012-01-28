#!/usr/bin/env python
# -*- coding:utf-8 -*-

import BaseBot
import time
import datetime

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

    def _is_command(self, status, command):
        if isinstance(command, (list, tuple)):
            for c in command:
                if not self._is_command(status, c):
                    return False
            return True
        elif isinstance(command, set):
            for c in command:
                if self._is_command(status, c):
                    return True
            return False    
        elif isinstance(command, (str, unicode)):
            return status.text.find(command)>=0
        elif callable(command):
            return commad(status)
        else:
            return False

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
        if not self._is_command(status, self._command):
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
        if not self._is_command(status, self._command):
            return False
        if self.is_allowed(status):
            raise BaseBot.BotShutdown
        return False

class history_hook(admin_hook):
    """連投規制機能"""
    def __init__(self, reply_limit, reset_cycle, limit_msg=None, allowed_users=None):
        super(history_hook, self).__init__(allowed_users)
        self.reply_limit = reply_limit
        self.reset_cycle = reset_cycle
        self.limit_msg = limit_msg
        self.reply_history = {}

    def __call__(self, bot, status):
        if not self.is_allowed(status):
            return False

        author = status.author.screen_name.lower()
        history = self.reply_history
        now = time.time()

        #履歴更新
        if author in history:
            if history[author]['count']==self.reply_limit and self.limit_msg:
                self.reply_to(u'%s [%s]' %
                              (self.limit_msg, bot.get_timestamp()),
                              status)
            history[author]['count'] += 1
            if history[author]['count']>self.reply_limit:
                return True
        else:
            history[author] = {
                'time': now,
                'count': 1,
                }

        #古い履歴は削除
        for name in history.keys():
            if now-history[name]['time']>self.reset_cycle:
                del history[name]

        return False
