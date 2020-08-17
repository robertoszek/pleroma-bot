# pleroma-twitter-info-grabber

Mirror one or multiple Twitter accounts in Pleroma/Mastodon.

## Introduction

After using the pretty cool [mastodon-bot](https://github.com/yogthos/mastodon-bot) for a while, I found it was lacking some actions which were of use to me. 

For precisely those cases I've written this Python project that automates them, asking such info to [Twitter's API](https://developer.twitter.com/en/docs/twitter-api/v1) and updating the relevant fields on the [Pleroma API](https://docs-develop.pleroma.social/backend/API/pleroma_api/) side.


So basically, it does the following:

* Retrieves **last 50 tweets** ```[TEXT-ONLY for now]``` and posts them on the Fediverse account if their timestamp is newer than the last post. 
* Gets the **display name** from Twitter and updates it in on the Fediverse account
* Gets the **profile picture** from Twitter and updates it on the Fediverse account
* Gets the **banner image** from Twitter and updates it on the Fediverse account
* Gets the **bio text** from Twitter and updates it on the Fediverse account
* Adds some **metadata fields** to the Fediverse account, pointing to the original Twitter account

## Usage
```console
$ python3 updateInfoPleroma.py [noProfile]
```
### Before running
You'll need to edit this section on ```updateInfoPleroma.py```:
```python
    user_dict = [{"username": 'WoolieWoolz', "token": 'emptyonpurpose'},
                 {"username": 'KyleBosman', "token": 'emptyonpurpose'}]
```
Changing the ```username``` to the desired one. You can add as many users as needed. The token is deliberately left with a nonsense value, it will stored on ```users/<username>/usercred.secret``` instead. It's a remnant of a previous version and will most probably be removed in future releases.

A important caveat to note is that the username **must be identical** to both the Twitter account and Fediverse account.

Also change the following to your Pleroma/Mastodon instance URL:
```python
pleroma_base_url = 'https://pleroma.robertoszek.xyz'
```
### Running
The first run will ask for:

* A [Twitter Bearer Token](https://developer.twitter.com/en/docs/authentication/api-reference/token)
* The user/users [Pleroma Bearer Tokens](https://tinysubversions.com/notes/mastodon-bot/)

They will then be stored at ```twittercred.secret``` and ```users/<username>/usercred.secret``` respectively and used in consequent runs from those files as primary source.

If the ```noProfile``` argument is passed, *only* new tweets will be posted. The profile picture, banner, display name and bio will **not** be updated on the Fediverse account.

### crontab entry example 
**(everyday at 6:15 AM)** update profile and **(every 10 min.)** post new tweets:
```bash
# Pleroma post tweets
*/10 * * * * cd /opt/pleroma-twitter-info-grabber/ && python3 updateInfoPleroma.py noProfile
# Pleroma update profile with Twitter info
15 6 * * * cd /opt/pleroma-twitter-info-grabber/ && python3 updateInfoPleroma.py
```
## Acknowledgements
These projects proved to be immensely useful, they are Python wrappers for the Mastodon API and Twitter API respectively:

* [Mastodon.py](https://github.com/halcy/Mastodon.py)
* [twitter-python](https://github.com/bear/python-twitter/)

They were part of the impetus for this project, challenging myself to not just import them and use them, instead opting to directly do the heavy lifting with built-in python modules. 

That and [mastodon-bot](https://github.com/yogthos/mastodon-bot) not working after upgrading the Pleroma instance I was admin on. This event lead to repurposing it and adding the tweet gathering and posting capabilities.

## Contributing

Patches, pull requests, and bug reports are more than [welcome](https://gitea.robertoszek.xyz/robertoszek/pleroma-twitter-info-grabber/issues/new), please keep the style consistent with the original source.


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
* ```Pleroma BE 2.0.50-2389-g7625e509-develop```
* ```Twitter API v1.1```