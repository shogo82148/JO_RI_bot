# -*- coding:utf-8 -*-

from tweepy.parsers import ModelParser
import json

def ReturnModel(**config):
    class APIMethod(object):
        payload_type = config.get('payload_type', None)
        payload_list = config.get('payload_list', False)
        allowed_param = config.get('allowed_param', [])
        method = config.get('method', 'GET')
        require_auth = config.get('require_auth', False)
        search_api = config.get('search_api', False)
        use_cache = config.get('use_cache', True)

        def __init__(self, api, func, args, kargs):
            self.api = api
            self.func = func
            self.args = args
            self.kargs = kargs
            self.parameters = {}

        def execute(self):
            api = self.api
            func = self.func
            args = self.args
            kargs = self.kargs
            result = func(api, *args, **kargs)
            content = json.dumps(result)
            return api.parser.parse(self, content)

    def wrapper(f):
        def _call(api, *args, **kargs):
            method = APIMethod(api, f, args, kargs)
            return method.execute()
        return _call

    return wrapper

class API(object):
    def __init__(self):
        self.parser = ModelParser()
        self._id = 0
        self._my_statuses = []

    @ReturnModel(payload_type='status')
    def update_status(self, status, in_reply_to_status_id=None, lat=None, long=None, source=None, place_id=None):
        status = getStatus(
            text = status,
            id = self.newId(),
            user = self._me(),
            in_reply_to_status_id = in_reply_to_status_id
            )
        self._my_statuses.insert(0, status)
        return status

    @ReturnModel(payload_type='status', payload_list=True)
    def user_timeline(self, id=None, user_id=None, screen_name=None,
                      since_id=None, max_id=None, count=None, page=None,
                      includes_rts=None, trim_user=None):
        if(id or user_id or screen_name):
            return []
        else:
            return self._my_statuses

    @ReturnModel(payload_type='user')
    def me(self):
        return self._me()

    def _me(self):
        return getUser(screen_name='bot', id=1, name="Bot")

    def newId(self):
        self._id += 1
        return self._id

    def getLatestId(self):
        return self._id

    def getStatus(self, text, user, **kargs):
        return getStatus(text, user, self.newId(), **kargs)

def getUser(
    screen_name = '',
    id = 0,
    name = None,
    **kargs):

    user = {
        "profile_sidebar_fill_color": "e0ff92",
        "profile_sidebar_border_color": "87bc44",
        "profile_background_tile": False,
        "created_at": "Wed May 23 06:01:13 +0000 2007",
        "profile_image_url": "http://example.com",
        "location": "Japan",
        "follow_request_sent": False,
        "profile_link_color": "0000ff",
        "is_translator": False,
        "contributors_enabled": False,
        "url": "http://example.com/",
        "favourites_count": 0,
        "utc_offset": 0,
        "profile_use_background_image": True,
        "listed_count": 0,
        "profile_text_color": "000000",
        "protected": False,
        "followers_count": 0,
        "lang": "ja",
        "notifications": False,
        "geo_enabled": False,
        "profile_background_color": "c1dfee",
        "verified": False,
        "description": False,
        "time_zone": "Tokyo",
        "profile_background_image_url": "http://example.com/",
        "friends_count": 0,
        "statuses_count": 0,
        "following": False,
        "show_all_inline_media": False,
        }
    for key, value in kargs.iteritems():
        user[key] = value
    user['id'] = id
    user['id_str'] = str(id)
    user['screen_name'] = screen_name
    user['name'] = name or screen_name
    return user

def getStatus(text, user, id, **kargs):
    status = {
        "coordinates": None,
        "created_at": "Sat Sep 10 22:23:38 +0000 2011",
        "truncated": False,
        "favorited": False,
        "contributors": None,
        "retweet_count": 0,
        "geo": None,
        "retweeted": False,
        "possibly_sensitive": False,
        "place": None,
        "source": "Web",
        "in_reply_to_user_id": None,
        "in_reply_to_user_id_str": None,
        "in_reply_to_status_id": None,
        "in_reply_to_status_id_str": None,
        "in_reply_to_screen_name": None,
        }
    for key, value in kargs.iteritems():
        status[key] = value
    status['text'] = text
    status['user'] = user
    status['id'] = id
    status['id_str'] = str(id)
    if status['in_reply_to_user_id']:
        status['in_reply_to_user_id_str'] = str(status['in_reply_to_user_id'])
    if status['in_reply_to_status_id']:
        status['in_reply_to_status_id_str'] = str(status['in_reply_to_status_id'])
    return status

