# Stork (pleroma-bot)

[![Build Status](https://travis-ci.com/robertoszek/pleroma-bot.svg?branch=develop)](https://app.travis-ci.com/github/robertoszek/pleroma-bot)
[![Version](https://img.shields.io/pypi/v/pleroma-bot.svg)](https://pypi.org/project/pleroma-bot/)
[![AUR version](https://img.shields.io/aur/version/python-pleroma-bot)](https://aur.archlinux.org/packages/python-pleroma-bot)
[![codecov](https://codecov.io/gh/robertoszek/pleroma-bot/branch/master/graph/badge.svg?token=0c4Gzv4HjC)](https://codecov.io/gh/robertoszek/pleroma-bot)
[![Python 3.6](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License](https://img.shields.io/github/license/robertoszek/pleroma-bot)](https://github.com/robertoszek/pleroma-bot/blob/master/LICENSE.md)

![Stork](img/stork-smaller.svg)

Mirror your favorite Twitter accounts in the Fediverse, so you can follow their updates from the comfort of your favorite instance. Or migrate your own to the Fediverse using a Twitter [archive](https://twitter.com/settings/your_twitter_data).

[![Documentation](img/docs.png)](https://robertoszek.github.io/pleroma-bot)

## Introduction

After using the pretty cool [mastodon-bot](https://github.com/yogthos/mastodon-bot) for a while, I found it was lacking some actions which were of use to me. 

For precisely those cases I've written this Python project that automates them, asking such info to [Twitter's API](https://developer.twitter.com/en/docs/twitter-api/v1) and updating the relevant fields on the [Pleroma API](https://docs-develop.pleroma.social/backend/API/pleroma_api/)/[Mastodon API](https://docs.joinmastodon.org/client/intro/) side.


## Features 

So basically, it does the following:
* Can parse a Twitter [archive](https://twitter.com/settings/your_twitter_data), moving all your tweets to the Fediverse
* Retrieves **tweets** and posts them on the Fediverse account if their timestamp is newer than the last post.
  * Can filter out RTs or not
  * Can filter out replies or not
* Media retrieval and upload of multiple **attachments**. This includes:
  * Video
  * Images
  * Animated GIFs 
  * Polls
* Retrieves **profile info** from Twitter and updates it in on the Fediverse account. This includes:
  * *Display name*
  * *Profile picture*
  * *Banner image*
  * *Bio text*
* Adds some **metadata fields** to the Fediverse account, pointing to the original Twitter account or custom text.

## Installation
### Using pip
```
$ pip install pleroma-bot
```
### Using a package manager
Here's a list of the available packages.

| Package type   | Link                                                    | Maintainer                                    |
|:--------------:|:-------------------------------------------------------:|:---------------------------------------------:|
| AUR (Arch)     | https://aur.archlinux.org/packages/python-pleroma-bot  | [robertoszek](https://github.com/robertoszek) |

## Usage
```console
$ pleroma-bot [-c CONFIG] [-l LOG] [--noProfile] [--daemon] [--forceDate [FORCEDATE]] [-a ARCHIVE]
```

```console
Bot for mirroring one or multiple Twitter accounts in Pleroma/Mastodon.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path of config file (config.yml) to use and parse. If
                        not specified, it will try to find it in the current
                        working directory.
  -d, --daemon          run in daemon mode. By default it will re-run every
                        60min. You can control this with --pollrate
  -p POLLRATE, --pollrate POLLRATE
                        only applies to daemon mode. How often to run the
                        program in the background (in minutes). By default is
                        60min.
  -l LOG, --log LOG     path of log file (error.log) to create. If not
                        specified, it will try to store it at your config file
                        path
  -n, --noProfile       skips Fediverse profile update (no background image,
                        profile image, bio text, etc.)
  --forceDate [FORCEDATE]
                        forces the tweet retrieval to start from a specific
                        date. The twitter_username value (FORCEDATE) can be
                        supplied to only force it for that particular user in
                        the config
  -s, --skipChecks      skips first run checks
  -a ARCHIVE, --archive ARCHIVE
                        path of the Twitter archive file (zip) to use for
                        posting tweets.
  --verbose, -v
  --version             show program's version number and exit
```
### Before running
You'll need the following:

* A [Twitter Bearer Token](https://developer.twitter.com/en/docs/authentication/api-reference/token)
* The user/users [Pleroma/Mastodon Bearer Tokens](https://tinysubversions.com/notes/mastodon-bot/)

If you plan on retrieving tweets from an account which has their tweets **protected**, you'll also need the following:
* Consumer Key and Secret. You'll find them on your project app keys and tokens section at [Twitter's Developer Portal](https://developer.twitter.com/en/portal/dashboard)
* Access Token Key and Secret.  You'll also find them on your project app keys and tokens section at [Twitter's Developer Portal](https://developer.twitter.com/en/portal/dashboard). 
Alternatively, you can obtain the Access Token and Secret by running [this](https://github.com/joestump/python-oauth2/wiki/Twitter-Three-legged-OAuth-Python-3.0) locally, while being logged in with a Twitter account which follows or is the owner of the protected account

### Configuration

Create a ```config.yml``` file in the same path where you are calling ```pleroma-bot``` (or use the `--config` argument to specify a different path). 

There's a config example in this repo called ```config.yml.sample``` that can help you when filling yours out.

For more information you can refer to the ["Configuration" page](https://robertoszek.github.io/pleroma-bot/gettingstarted/configuration/) on the docs.

Here's what a minimal config looks like:
```yaml
# Change this to your target Fediverse instance
pleroma_base_url: https://pleroma.instance
# How many tweets to get in every execution
# Twitter's API hard limit is 3,200
max_tweets: 40
# Twitter bearer token
twitter_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
  # Mastodon/Pleroma bearer token
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Running

If you're running the bot for the first time it will ask you for the date you wish to start retrieving tweets from (it will gather all from that date up to the present). 
If you leave it empty and just press enter it will default to the oldest date that Twitter's API allows ('```2010-11-06T00:00:00Z```') for tweet retrieval.

To force this behaviour in future runs you can use the ```--forceDate``` argument (be careful, no validation is performed with the already posted toots/posts by that Fediverse account and you can end up with duplicates posts/toots!).

Additionally, you can provide a ```twitter_username``` if you only want to force the date for one user in your config.

For example:

```console
$ pleroma-bot --forceDate WoolieWoolz
```

If the --noProfile argument is passed, the profile picture, banner, display name and bio will **not** be updated on the Fediverse account. However, it will still gather and post the tweets following your config's parameters.

NOTE: An ```error.log``` file will be created at the path from which ```pleroma-bot``` is being called.

### crontab entry example 
**(everyday at 6:15 AM)** update profile and **(every 10 min.)** post new tweets:
```bash
# Post tweets every 10 min
*/10 * * * * cd /home/robertoszek/myvenv/ && . bin/activate && pleroma-bot noProfile

# Update pleroma profile with Twitter info every day at 6:15 AM
15 6 * * * cd /home/robertoszek/myvenv/ && . bin/activate && pleroma-bot
```

## Screenshots

![Screenshot](img/cmd.png)


![Screenshot](img/screenshot.png)

## Acknowledgements
These projects proved to be immensely useful, they are Python wrappers for the Mastodon API and Twitter API respectively:

* [Mastodon.py](https://github.com/halcy/Mastodon.py)
* [twitter-python](https://github.com/bear/python-twitter)

They were part of the impetus for this project, challenging myself to not just import them and use them, instead opting to directly do the heavy lifting with built-in python modules. 

That and [mastodon-bot](https://github.com/yogthos/mastodon-bot) not working after upgrading the Pleroma instance I was admin on 😅. This event lead to repurposing it and adding the tweet gathering and posting capabilities.

## Contributing

Patches, pull requests, and bug reports are more than [welcome](https://github.com/robertoszek/pleroma-bot/issues/new/choose), please keep the style consistent with the original source.


## License

MIT License

Copyright (c) 2022 Roberto Chamorro / project contributors

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
* ```Pleroma BE 2.2.50-711-g100e34b4-develop```
* ```Mastodon v3.2.1```
* ```Twitter API v1.1 and v2```
