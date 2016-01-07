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

from optparse import OptionParser
parser = OptionParser()

parser.add_option("--text", dest="text", help="use 'text' file from config as source", action="store_true", default=False)
parser.add_option("--kindle", dest="kindle", help="use 'kindle' from config as source", action="store_true", default=False)
parser.add_option("--skip_learned", dest="skip_learned", help="skip learned words", action="store_true", default=False)


(options, args) = parser.parse_args()


export_type = sys.argv[1]
if options.text:
    handler = word.Text(config.sources.get('text'))
elif options.kindle:
    handler = word.Kindle(config.sources.get('kindle'))
else:
    raise Exception('unsupported type')

handler.read()

lingualeo = service.Lingualeo(email, password)
print 'auth ... ',
lingualeo.auth()
print 'ok'

words = list(set(handler.get()))

i = 0

learned_words = [word['word_value'] for word in lingualeo.get_learned_words()]

print len(learned_words), 'words learnt'

added_words = [word['word_value'] for word in lingualeo.get_user_dict_words(groupId)]

print len(added_words), 'words in group', groupId

already_learnt = 0
already_added = 0

for word in words:
    word = word.lower()
    i += 1

    print i, 'of', len(words), ':',

    if len(word) == 1:
        print 'skip', word
        continue

    if options.skip_learned and word in learned_words:
        print 'already learnt, skip', word
        already_learnt += 1
        continue

    if word in added_words:
        print 'already added, skip', word
        already_added += 1
        continue

    try:
        leo_word, translate = lingualeo.get_translates(word)

        
        if translate is None:
            print 'not found', word
            continue

        lingualeo.add_word(
            translate["word"], translate["tword"], translate['word_id'], translate['translate_id'], 
            translate['speech_part_id'], groupId=groupId)

        if translate["is_exist"]:
            result = "Add word: "
        else:
            result = "Already exists: "

        if translate["is_cached"]:
            result = '[cached] ' + result

        result = result + word

        print result, translate['translate_id']

    except KeyboardInterrupt:
        break;
    except:
        print word, traceback.format_exc()

print 'already learnt', already_learnt
print 'already added', already_added

