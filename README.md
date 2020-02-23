# Real Tweet Redact Bot

This bot finds real, recent tweets that contain keywords, and reposts a
redacted version. All twitter handles and urls should be redacted, along
with a random selection of words. After that, some of the words will be
'jiggled' to become a word with a similar meaning.

## Requirements

* `Python3`
* An internet connection
* A bash shell to run `install.sh`, or you can run the commands yourself.
* A twitter account with developer access

## Installation
All of the installation can be done by running `install.sh`

    git clone https://github.com/hitcherland/redact_twitter_bot
    cd redact_twitter_bot
    bash ./install.sh

## Configuration

To configure the bot, copy `sample_config.json` to `config.json` and edit it
to contain your authorization values. You can also adjust some of the bots
redaction variables.

    cp sample_config.json config.json
    vim config.json
    ...
## Bot Variables
### `keywords`
A list of words which will branch out to similar words (as far as nltk is
concerned), which will be used to find live tweets with.

### `redact_word_ratio`
The chance any word in the tweet has of being replaced with a redacted version.
Should be between 0 and 1, where 0 is none and 1 is all words.

### `redact_noun_ratio`
The chance any noun in the tweet has of being replaced with a redacted version.
This runs after redact_word, to make sure we redact 
Should be between 0 and 1, where 0 is none and 1 is all nouns.

### `jiggle_rate`
How many words in the sentence, after redaction, will be jiggled to a new,
similar word.
Should be between 0 and 1, where 0 is none and 1 is all remaining words.
