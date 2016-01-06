#!/usr/bin/env python
# -*- coding: utf-8 -*-
import word
import config
import service
import sys
import traceback

from service import cache_get, cache_set

email = config.auth.get('email')
password = config.auth.get('password')
groupId = config.sources.get('groupId')

try:
    export_type = sys.argv[1]
    if export_type == 'text':
        handler = word.Text(config.sources.get('text'))
    elif export_type == 'kindle':
        handler = word.Kindle(config.sources.get('kindle'))
    else:
        raise Exception('unsupported type')

    handler.read()

    lingualeo = service.Lingualeo(email, password)
    print 'auth ... ',
    lingualeo.auth()
    print 'ok'

    for word in handler.get():
        word = word.lower()
        leo_word, translate = lingualeo.get_translates(word)

        
        is_exists = cache_get('is_exists.cache.pickle', word)

        if translate is None:
            print 'not found', word
            continue
        if is_exists:
            print 'Detect exists:', word
            continue
        lingualeo.add_word(
            translate["word"], translate["tword"], translate['word_id'], translate['translate_id'], 
            translate['speech_part_id'], groupId=groupId)

        cache_set('is_exists.cache.pickle', word, True)

        if translate["is_exist"]:
            result = "Add word: "
        else:
            result = "Already exists: "

        if translate["is_cached"]:
            result = '[cached] ' + result

        result = result + word

        print result, translate['translate_id']


except:
    print traceback.format_exc()
