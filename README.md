# pleroma-twitter-info-grabber

[![Build Status](https://travis-ci.com/robertoszek/pleroma-twitter-info-grabber.svg?branch=develop)](https://travis-ci.com/robertoszek/pleroma-twitter-info-grabber)
[![Version](https://img.shields.io/pypi/v/pleroma-bot.svg)](https://pypi.org/project/pleroma-bot/)
[![codecov](https://codecov.io/gh/robertoszek/pleroma-twitter-info-grabber/branch/master/graph/badge.svg?token=0c4Gzv4HjC)](https://codecov.io/gh/robertoszek/pleroma-twitter-info-grabber)
[![Python 3.6](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Requires.io (branch)](https://img.shields.io/requires/github/robertoszek/pleroma-twitter-info-grabber/master)](https://requires.io/github/robertoszek/pleroma-twitter-info-grabber/requirements/?branch=master)
[![License](https://img.shields.io/github/license/robertoszek/pleroma-twitter-info-grabber)](https://github.com/robertoszek/pleroma-twitter-info-grabber/blob/master/LICENSE.md)

Mirror one or multiple Twitter accounts in Pleroma/Mastodon.

## Introduction

After using the pretty cool [mastodon-bot](https://github.com/yogthos/mastodon-bot) for a while, I found it was lacking some actions which were of use to me. 

For precisely those cases I've written this Python project that automates them, asking such info to [Twitter's API](https://developer.twitter.com/en/docs/twitter-api/v1) and updating the relevant fields on the [Pleroma API](https://docs-develop.pleroma.social/backend/API/pleroma_api/) side.


So basically, it does the following:

* Retrieves **last 'max_tweets' tweets** and posts them on the Fediverse account if their timestamp is newer than the last post. 
* Gets the **display name** from Twitter and updates it in on the Fediverse account
* Gets the **profile picture** from Twitter and updates it on the Fediverse account
* Gets the **banner image** from Twitter and updates it on the Fediverse account
* Gets the **bio text** from Twitter and updates it on the Fediverse account
* Adds some **metadata fields** to the Fediverse account, pointing to the original Twitter account

## Installation
```
$ pip install pleroma-bot
```
## Usage
```console
$ pleroma-bot [noProfile]
```
### Before running
You'll need the following:

* A [Twitter Bearer Token](https://developer.twitter.com/en/docs/authentication/api-reference/token)
* The user/users [Pleroma Bearer Tokens](https://tinysubversions.com/notes/mastodon-bot/)

Create a ```config.yml``` file in the same path where you are calling ```pleroma-bot```. There's a config example in this repo called ```config.yml.sample``` that can help you when filling yours out:
```yaml
twitter_base_url: https://api.twitter.com/1.1
# Change this to your Fediverse instance
pleroma_base_url: https://pleroma.robertoszek.xyz
# How many tweets to get in every execution
# Twitter's API hard limit is 3,200
max_tweets: 40
# Twitter bearer token
twitter_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# List of users and their attributes
users:
- twitter_username: KyleBosman
  pleroma_username: KyleBosman
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  # If you want to add a link to the original status or not
  signature: true
  # If you want to download Twitter attachments and add them to the Pleroma posts
  media_upload: true
  # If twitter links should be changed to nitter.net ones
  nitter: true
  # If mentions should be transformed to links to the mentioned Twitter profile
  rich_text: true
  # visibility of the post. Must one of the following: public, unlisted, private, direct
  visibility: "unlisted"
  # Force all posts for this account to be sensitive or not
  # The NSFW banner for the instance will be shown for attachments as a warning if true
  # If not defined, the original tweet sensitivity will be used on a tweet by tweet basis
  sensitive: false
  support_account: robertoszek
  # you can use any attribute from 'user' inside a string with {{ attr_name }} and it will be replaced
  # with the attribute value. e.g. {{ support_account }}
  bio_text: "\U0001F916 BEEP BOOP \U0001F916 \nI'm a bot that mirrors {{ twitter_username }} Twitter's\
    \ account. \nAny issues please contact @{{ support_account }} \n \n " # username will be replaced by its value
  # Optional metadata fields and values for the Pleroma profile
  fields:
  - name: "\U0001F426 Birdsite"
    value: "{{ twitter_url }}"
  - name: "Status"
    value: "I am completely operational, and all my circuits are functioning perfectly."
  - name: "Source"
    value: "https://gitea.robertoszek.xyz/robertoszek/pleroma-twitter-info-grabber"
- twitter_username: arstechnica
  pleroma_username: mynewsbot
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  signature: true
  nitter: true
  media_upload: false
  pleroma_url: https://another.pleroma.instance
  max_tweets: 50
  bio_text: "\U0001F916 BEEP BOOP \U0001F916 \n I'm a bot that mirrors {{ twitter_username }} Twitter's\
    \ account. \n Any issues please contact @robertoszek \n \n "
```
Changing the ```users``` to the desired ones. You can add as many users as needed.

Also change the following to your Pleroma/Mastodon instance URL:
```yaml
pleroma_base_url: https://pleroma.robertoszek.xyz
```
### Running

If the ```noProfile``` argument is passed, *only* new tweets will be posted. The profile picture, banner, display name and bio will **not** be updated on the Fediverse account.

NOTE: An ```error.log``` file will be created at the path from which ```pleroma-bot``` is being called.

### crontab entry example 
**(everyday at 6:15 AM)** update profile and **(every 10 min.)** post new tweets:
```bash
# Post tweets every 10 min
*/10 * * * * cd /home/robertoszek/myvenv/ && . bin/activate && pleroma-bot noProfile

# Update pleroma profile with Twitter info every day at 6:15 AM
15 6 * * * cd /home/robertoszek/myvenv/ && . bin/activate && pleroma-bot
```
## Acknowledgements
These projects proved to be immensely useful, they are Python wrappers for the Mastodon API and Twitter API respectively:

* [Mastodon.py](https://github.com/halcy/Mastodon.py)
* [twitter-python](https://github.com/bear/python-twitter)

They were part of the impetus for this project, challenging myself to not just import them and use them, instead opting to directly do the heavy lifting with built-in python modules. 

That and [mastodon-bot](https://github.com/yogthos/mastodon-bot) not working after upgrading the Pleroma instance I was admin on 😅. This event lead to repurposing it and adding the tweet gathering and posting capabilities.

## Contributing

Patches, pull requests, and bug reports are more than [welcome](https://github.com/robertoszek/pleroma-twitter-info-grabber/issues/new/choose), please keep the style consistent with the original source.


## License

MIT License

Copyright (c) 2020 Roberto Chamorro / project contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

**Tested and confirmed working against** :
* ```Pleroma BE 2.0.50-2547-g5c2b6922-develop```
* ```Twitter API v1.1```
