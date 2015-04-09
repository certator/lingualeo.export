#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import json, time
import codecs, simplejson, pickle, os

from cookielib import CookieJar

def cache_get(fname, key):
    if not os.path.exists(fname):
        return None
    with codecs.open(fname, 'r', ) as f:
        cache = pickle.load(f)
    return cache.get(key, None)

def cache_set(fname, key, value):
    if os.path.exists(fname):
        with codecs.open(fname, 'r', ) as f:
            cache = pickle.load(f)
    else:
        cache = {}
    cache[key] = value
    s = pickle.dumps(cache, ) #ensure_ascii=False
    with codecs.open(fname, 'w', ) as f:
        f.write(s)

class Lingualeo:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cj = CookieJar()

    def auth(self):
        url = "http://api.lingualeo.com/api/login"
        values = {
            "email": self.email,
            "password": self.password
        }

        return self.get_content(url, values)

    def add_word(self, word, tword, word_id=None):
        url = "http://api.lingualeo.com/addword"
        values = {
            "word": word,
            "tword": tword,            
            #"context": "sentence here",
            #"port": 1001,
        }
        self.get_content(url, values)

        if word_id and False:
            url = "http://lingualeo.com/ru/userdict3/addWordsToGroup"
            values = {
                "all": '0',
                "groupId": "dictionary",
                "filter": "all",
                "wordIds": str(word_id),
                "wordType": "0",
                "wordSetId": "1202",
                #all=0&groupId=dictionary&filter=all&wordIds=25397%2C41417%2C110651&search=&wordType=0&wordSetId=1152
            }
            print '>', self.get_content(url, values), '<'   
    

    def get_translates(self, word):
        url = "http://api.lingualeo.com/gettranslates?word=" + urllib.quote_plus(word)




        cached = False
        result = cache_get('gettranslates.cache.pickle', word)
        if result is None:
            result = self.get_content(url, {})
            #print result, [word]
            cache_set('gettranslates.cache.pickle', word, result)
        translates = sorted(result["translate"], key=lambda i: -i['votes'])
        if len(translates) == 0:
            return None
        translate = translates[0]
        #print '>>>>>'
        #print result
        #print translate
        #print sorted(result["translate"], key=lambda i: -i['votes'])
        return {
            "is_exist": translate["is_user"],
            "is_cached": cached,
            "word": word,
            "tword": translate["value"].encode("utf-8"),
            "id": translate["id"],
        }

    last_rq = time.time()
    throttle = 0.5

    def get_content(self, url, values):
        time.sleep(max(0, self.throttle - (time.time() - self.last_rq)))
        self.last_rq = time.time()
        data = urllib.urlencode(values)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        req = opener.open(url, data)

        return json.loads(req.read())

'''
{u'is_user': 0, u'word_top': 0, u'word_forms': [], u'transcription': None, u'sound_url': u'http://d2x1jgnvxlnz25.cloudfront.net/v2/0/mXM=.mp3', u'translate_source': u'base', u'translate': [{u'is_user': 0, u'votes': 0, u'id': 0, u'value': u'?\u044b', u'pic_url': u''}], u'error_msg': u'', u'word_id': 0}

{'\x99s': {u'error_msg': u'',
  u'is_user': 0,
  u'sound_url': u'http://d2x1jgnvxlnz25.cloudfront.net/v2/0/mXM=.mp3',
  u'transcription': None,
  u'translate': [{u'id': 0,
    u'is_user': 0,
    u'pic_url': u'',
    u'value': u'?\u044b',
    u'votes': 0}],
  u'translate_source': u'base',
  u'word_forms': [],
  u'word_id': 0,
  u'word_top': 0}}

'''
