#!/usr/bin/env python
# -*- coding:utf-8 -*-

import tweepy
import json
from tweepy import User
from tweepy import Status

class StreamListener(tweepy.StreamListener):
    """ tweepyのStreamListenerのラッパ """
    def __init__(self):
        self.__api = tweepy.API()

    def on_data(self, data):
        if not data:
            return
        json_data = json.loads(data)
        api = self.__api
        
        if not isinstance(json_data, dict):
            return

        if 'event' in json_data:
            if json_data['event']=='follow':
                target = User.parse(api, json_data["target"])
                source = User.parse(api, json_data["source"])
                if self.on_follow(target, source) is False:
                    return False
            elif json_data['event']=='favorite':
                target = Status.parse(api, json_data['target_object'])
                source = User.parse(api, json_data['source'])
                if self.on_favorite(target, source) is False:
                    return False
            elif json_data['event']=='unfavorite':
                target = Status.parse(api, json_data['target_object'])
                source = User.parse(api, json_data['source'])
                if self.on_unfavorite(target, source) is False:
                    return False
        elif 'delete' in json_data:
            delete = json_data['delete']['status']
            if self.on_delete(delete['id'], delete['user_id']) is False:
                return False
        elif 'in_reply_to_status_id' in json_data:
            status = Status.parse(api, json_data)
            if self.on_status(status) is False:
                return False
        elif 'limit' in json_data:
            if self.on_limit(json_data['limit']['track']) is False:
                return False

    def on_follow(self, target, source):
        return

    def on_favorite(self, target, source):
        return

    def on_unfavorite(self, target, source):
        return


