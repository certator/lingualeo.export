#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2

import requests

import json, time
import codecs, simplejson, pickle, os

from cookielib import CookieJar

from peewee import *
import os, sys, datetime, copy

import logging

def turn_on_requests_debugging():
    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig() 
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

    requests.get('https://httpbin.org/headers')


#turn_on_requests_debugging()



os.environ.setdefault('db_root', '.')

db = SqliteDatabase(os.environ['db_root'] + '/cache_database.db', threadlocals=True)

class BaseModel(Model):
    class Meta:
        database = db

class CacheRecord(BaseModel):
    created_date = DateTimeField(default=datetime.datetime.now, index=True)
    last_changed = DateTimeField(default=datetime.datetime.now, index=True)
    last_access = DateTimeField(default=datetime.datetime.now, index=True)

    key = CharField(null=False, default=None, index=True, unique=True)
    value = TextField(null=True, default=None)

db.connect()
try:
    db.create_tables([CacheRecord, ])
except:
    pass


def fs_cache_get(fname, key):
    if not os.path.exists(fname):
        return None
    #if fname in LoadedCache.caches:
    #    if key in LoadedCache.caches[fname]:
    #        return LoadedCache.caches[fname][key]
    with codecs.open(fname, 'r', ) as f:
        cache = pickle.load(f)
        LoadedCache.caches[fname] = cache
    return cache.get(key, None)

def fs_cache_set(fname, key, value):
    if os.path.exists(fname):
        with codecs.open(fname, 'r', ) as f:
            cache = pickle.load(f)
    else:
        cache = {}
    cache[key] = value
    s = pickle.dumps(cache, ) #ensure_ascii=False
    with codecs.open(fname, 'w', ) as f:
        f.write(s)

def db_cache_get(fname, key):
    key = fname + ":" + key
    for cacheRecord in CacheRecord.select().where(CacheRecord.key == key):
        return json.loads(cacheRecord.value)
    return None

def db_cache_set(fname, key, value):
    key = fname + ":" + key
    cacheRecord, created = CacheRecord.create_or_get(key = key)
    cacheRecord.value = json.dumps(value)
    cacheRecord.save()

cache_get = db_cache_get
cache_set = db_cache_set

class Lingualeo:

    headers = {
        'User-Agent' :'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0' ,
        'Accept' :'*/*' ,
        'Accept-Language' :'en-US,en;q=0.5' ,
        'Content-Type' :'application/x-www-form-urlencoded; charset=UTF-8' ,
        'X-Requested-With' :'XMLHttpRequest' ,
        'Connection' :'keep-alive' ,
        'Pragma' :'no-cache' ,
        'Cache-Control' :'no-cache' ,
    }


    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cj = CookieJar()

    def auth(self):
        url = "https://api.lingualeo.com/api/login"
        values = {
            "email": self.email,
            "password": self.password
        }

        return self.get_content(url, values, method='get')

    def add_word(self, word, tword, word_id=None, translate_id=None, speech_part_id=None, groupId=None):
        '''
        url = "http://api.lingualeo.com/addword"
        values = {
            "word": word,
            "tword": tword,            
            #"context": "sentence here",
            #"port": 1001,
        }
        self.get_content(url, values)
        '''

        if word_id:
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
            url = "https://lingualeo.com/userdict3/addWord"
            url = "https://lingualeo.com/ru/userdict3/addWord"
            values = {
                "word_id": str(word_id),
                "user_word_value": word,
                "translate_id": str(translate_id),
                "translate_value": tword,

                #"speech_part_id": str(speech_part_id),
                "speech_part_id": 0,
                "from_syntrans_id": "",
                "to_syntrans_id": "",
            }

            if not groupId is None:
                values.update({"groupId": str(groupId)})

            #print '>>', values
            #print '>', self.get_content2(url, values, headers=headers), '<'  
            headers =  copy.deepcopy(self.headers)
            headers['Referer'] = 'https://lingualeo.com/ru/glossary/learn/' + str(groupId) 
            r = self.get_content2(url, values, headers=self.headers)  
            if r['error_msg'] != '':
                raise Exception(r['error_msg'])


    def get_translates(self, word):
        url = "https://lingualeo.com/userdict3/getTranslations?word_value=" + urllib.quote_plus(word) + "&groupID=&_=" + str(time.time()*1000.0)




        cached = False
        result = cache_get('gettranslates.cache.pickle', word)
        if result is None:
            result = self.get_content(url, {})
            #print result, [word]
            cache_set('gettranslates.cache.pickle', word, result)
        #print result

        if result['error_msg'] != '':
            raise Exception(result['error_msg'])

        translates = sorted(result["userdict3"]['translations'], key=lambda i: -i['translate_votes'])
        if len(translates) == 0:
            return result, None
        translate = translates[0]
        #print '>>>>>'
        #print result
        #print translate
        #print sorted(result["translate"], key=lambda i: -i['votes'])
        return result, {
            "is_exist": translate["is_user"],
            "is_cached": cached,
            "word": word,
            "tword": translate["translate_value"].encode("utf-8"),
            "word_id": result["userdict3"]['word_id'],
            "translate_id": translate["translate_id"],
            'speech_part_id': translate["speech_part_id"],
        }   


    def query_user_dict(self, query, referer):
        url = "https://lingualeo.com/userdict/json"
        params = copy.deepcopy(query)
        page = 1

        words = []

        headers =  copy.deepcopy(self.headers)
        headers['Referer'] = referer


        while True:
            params['page'] = str(page)
            r = self.get_content2(url, params, headers=headers)  
            if r['error_msg'] != '':
                raise Exception(r['error_msg'])
            if len(r['userdict3']) == 0:
                break
            for date_range in r['userdict3']:
                words += date_range['words']
            page += 1
        return words
    
    def get_learned_words(self):     
        return self.query_user_dict({
                'sortBy': 'date',
                'wordType': '0',
                'filter': 'learned',
                'groupId': 'dictionary',
            }, 'https://lingualeo.com/ru/glossary/learn/dictionary')

    def get_user_dict_words(self, groupId):     
        return self.query_user_dict({
                'sortBy': 'date',
                'wordType': '0',
                'filter': 'all',
                'groupId': str(groupId),
            }, 'https://lingualeo.com/ru/glossary/learn/' + str(groupId))



    last_rq = time.time()
    throttle = 0.5

    def get_content(self, url, values, method='post'):
        time.sleep(max(0, self.throttle - (time.time() - self.last_rq)))
        self.last_rq = time.time()
        data = urllib.urlencode(values)

        opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj))

        req = opener.open(url, data)

        return json.loads(req.read())

    def get_content2(self, url, values, method='post', headers=[]):
        time.sleep(max(0, self.throttle - (time.time() - self.last_rq)))
        self.last_rq = time.time()
        data = urllib.urlencode(values)


        #print url, data

        if method == 'post':
            req = requests.post(url, data, cookies=self.cj, headers=headers)
        else:
            req = requests.get(url, data, cookies=self.cj)
        #print req.content

        return json.loads(req.content)


