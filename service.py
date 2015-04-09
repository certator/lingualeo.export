#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import json
import codecs, simplejson

from cookielib import CookieJar

def cache_get(fname, key):
    with codecs.open(fname, 'r', 'utf8') as f:
        cache = simplejson.load(f)
    return cache.get(key, None)

def cache_set(fname, key, value):
    with codecs.open(fname, 'r', 'utf8') as f:
        cache = simplejson.load(f)
    cache[key] = value
    s = simplejson.dumps(cache, indent=2, ensure_ascii=False)
    with codecs.open(fname, 'w', 'utf8') as f:
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

        if word_id:
            url = "http://lingualeo.com/userdict3/addWordsToGroup"
            values = {
                "all": '0',
                "groupId": "dictionary",
                "filter": "all",
                "wordIds": str(word_id),
                "wordType": "0",
                "wordSetId": "1152",
                #all=0&groupId=dictionary&filter=all&wordIds=25397%2C41417%2C110651&search=&wordType=0&wordSetId=1152
            }
            print '>', self.get_content(url, values), '<'   
    

    def get_translates(self, word):
        url = "http://api.lingualeo.com/gettranslates?word=" + urllib.quote_plus(word)




        cached = False
        result = cache_get('gettranslates.cache.json', word)
        if result is None:
            result = self.get_content(url, {})
            cache_set('gettranslates.cache.json', word, result)
        translate = sorted(result["translate"], key=lambda i: i['votes'])[0]
        print result, translate, sorted(result["translate"], key=lambda i: -i['votes'])
        return {
            "is_exist": translate["is_user"],
            "is_cached": cached,
            "word": word,
            "tword": translate["value"].encode("utf-8"),
            "id": translate["id"],
        }


    def get_content(self, url, values):
        data = urllib.urlencode(values)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        req = opener.open(url, data)

        return json.loads(req.read())
