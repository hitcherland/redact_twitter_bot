#!/usr/bin/env python
"""A twitter bot that grabs a random recent tweet and redacts it"""

import logging
import json
import os
import random
import re
import sys
import requests
from requests_oauthlib import OAuth1
from textblob import TextBlob, Word

class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result

handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
LOG = logging.Logger(__file__, level=os.environ.get('LOGLEVEL', 'INFO'))
LOG.addHandler(handler)

DEFAULT_KEYWORDS = ['suspicious', 'weird', 'strange', 'odd', 'unusual',
                    'creepy']
RETRY_LIMIT = 5

def get_potential_search_terms(*words):
    '''Uses nltk (via textblob) to get words similar to the keywords'''
    potential_search_terms = []
    for word in words:
        potential_search_terms.append(word)
        nltk_word = Word(word)
        for synset in nltk_word.synsets:
            for lemma in synset.lemmas():
                potential_search_terms.append(lemma.name())

    return potential_search_terms

def redact_tweet(text, word_ratio=0.3, noun_ratio=0.7):
    """Replaces random words/nouns with \u2588 at varying rates"""
    def replace_usernames(match):
        return '@' + '\u2588' * (len(match.group()) - 1)

    def replace_urls(match):
        return match.group(1) + '\u2588' * (len(match.group(2)))

    blob = TextBlob(text)
    words = blob.words
    nouns = blob.noun_phrases

    text = re.sub(r'@(\w+)', replace_usernames, text)
    text = re.sub(r'\b(https?://)(\S+)', replace_urls, text)

    for word in random.choices(words, k=int(word_ratio * len(words))):
        text = re.sub(rf'\b{word}\b', '\u2588' * len(word), text,
                      flags=re.IGNORECASE)

    for noun in random.choices(nouns, k=int(noun_ratio * len(nouns))):
        text = re.sub(rf'\b{noun}\b', '\u2588' * len(noun), text,
                      flags=re.IGNORECASE)

    return text

def jiggle_words(text, jiggle_rate=0.5):
    """Replaces words in the text with other, similar words"""
    blob = TextBlob(text)
    words = blob.words
    words = [w for w in blob.words if '\u2588' not in w and ' ' not in w]
    words = random.choices(words, k=int(len(words) * jiggle_rate))
    for word in words:
        word_set = []
        for synset in word.synsets:
            for lemma in synset.lemmas():
                if lemma.name() != word:
                    word_set.append(lemma.name())

        if word_set:
            new_word = random.choice(word_set)
            text = re.sub(rf'\b{word}\b', new_word, text)

    return text

def get_random_tweet(auth, potential_search_terms):
    """Get a random tweet that contains on of the potential search terms"""
    url = 'https://api.twitter.com/1.1/search/tweets.json'
    response_json = None

    retries = 0
    while retries < RETRY_LIMIT:
        resp = requests.get(url, auth=auth, params={
            'q': random.choice(potential_search_terms),
            'result_type': 'recent',
            'tweet_mode': 'extended',
        })

        response_json = resp.json()

        if 'errors' not in response_json:
            return random.choice(response_json['statuses'])

        retries += 1

def send_tweet(auth, text):
    """sends a tweet"""
    url = 'https://api.twitter.com/1.1/statuses/update.json'
    resp = requests.post(url, auth=auth, params={
        'status': text
    })
    return resp.json()


def main(keywords=None, authorization=None, redact_word_ratio=0.3,
         redact_noun_ratio=0.7, jiggle_rate=0.2, **kwargs):
    '''Get one tweet, redact it and retweet it'''
    #pylint: disable=unused-argument
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    try:
        auth = OAuth1(authorization['consumer key'],
                      authorization['consumer secret'],
                      authorization['token key'],
                      authorization['token secret'])
    except TypeError:
        LOG.error('No authorization items defined')
        return 1
    except KeyError as exception:
        LOG.error('Required authorization item "%s" missing',
                  exception.args[0])
        return 2

    potential_search_terms = get_potential_search_terms(*keywords)
    tweet = get_random_tweet(auth, potential_search_terms)
    text = tweet['full_text']
    LOG.info("using tweet: %d", tweet['id'])
    LOG.info("original: %s", text)

    redacted_text = redact_tweet(text, redact_word_ratio, redact_noun_ratio)
    LOG.info("redacted: %s", redacted_text)

    jiggled_text = jiggle_words(redacted_text, jiggle_rate)
    LOG.info("jiggled: %s", jiggled_text)

    resp = send_tweet(auth, jiggled_text)
    if 'errors' in resp:
        LOG.error('Failed to update status: %s', resp['errors'])
    else:
        LOG.info('Updated status, id = %d', resp['id'])

    return 0

if __name__ == '__main__':
    os.environ['NLTK_DATA'] = 'nltk_data'

    CONFIG_PATH = 'config.json'
    if len(sys.argv) > 1:
        CONFIG_PATH = sys.argv[1]

    with open(CONFIG_PATH) as fh:
        CONFIG = json.load(fh)

    sys.exit(main(**CONFIG))
