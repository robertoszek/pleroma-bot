#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2020 Roberto Chamorro / project contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Special thanks to
# https://github.com/bear/python-twitter/
# and
# https://github.com/halcy/Mastodon.py

import os
import sys
import string
import random
import requests
import shutil
import re
import mimetypes
import json

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from datetime import datetime

# Parameter to choose whether to update bio, avatar and banner or not - save some bandwidth
try:
    arg = sys.argv[1]
except IndexError:
    arg = ""
    print(f"Usage: {sys.argv[0]} [noProfile]")


def guess_type(media_file):
    mime_type = None
    try:
        mime_type = magic.from_file(media_file, mime=True)
    except AttributeError:
        mime_type = mimetypes.guess_type(media_file)[0]
    return mime_type


def random_string(length: int) -> str:
    """Returns a string of random characters of length 'length'
    
    Parameters
    ----------
    length: str, mandatory
        How long the string to return must be

    Returns
    -------
    str
        a string of length 'length' formed with random alpha-numerical characters
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def main():
    # TODO: Refactor main function and split it up in smaller pieces
    user_dict = [{"username": 'WoolieWoolz', "token": 'emptyonpurpose'},
                 {"username": 'KyleBosman', "token": 'emptyonpurpose'}]

    pleroma_base_url = 'https://pleroma.robertoszek.xyz'
    twitter_base_url = 'https://api.twitter.com/1.1'
    # TODO: find script path and make all paths relative to it
    
    # Twitter bearer token
    twitter_secret = os.path.join('twittercred.secret')
    if not os.path.isfile(twitter_secret):
        bearer_token = ""
        while not bearer_token:
            bearer_token = input('Twitter bearer token not found, please enter it to continue:')
        with open(twitter_secret, 'w') as token_file:
            token_file.write(bearer_token)
    else:
        with open(twitter_secret, 'r') as token_file:
            bearer_token = token_file.readline().rstrip()

    for user in user_dict:
        twitter_url = "http://nitter.net/" + user['username']
        # Set up files structure
        base_path = 'users'
        user_path = os.path.join(base_path, user['username'])
        tweets_temp_path = os.path.join(user_path, 'tweets')
        avatar_path = os.path.join(user_path, 'profile.jpg')
        header_path = os.path.join(user_path, 'banner.jpg')
        secret_path = os.path.join(user_path, 'usercred.secret')

        if not os.path.isdir('tweets'):
            os.mkdir('tweets')
        if not os.path.isdir(base_path):
            os.mkdir(base_path)
        if not os.path.isdir(user_path):
            os.mkdir(user_path)
        if not os.path.isfile(secret_path):
            user['token'] = ""
            while not user['token']:
                user['token'] = input('Pleroma token not found for user ' \
                                      + user['username'] + ', please enter it to continue:')
            with open(secret_path, 'w') as token_file:
                token_file.write(user['token'])
        else:
            with open(secret_path, 'r') as token_file:
                user['token'] = token_file.readline().rstrip()

        if not os.path.isdir(tweets_temp_path):
            os.mkdir(tweets_temp_path)
        # Auth
        header_pleroma = {"Authorization": "Bearer " + user['token']}
        header_twitter = {"Authorization": "Bearer " + bearer_token}
        
        """
        Compare and post only new tweets to Pleroma
        """

        # Get last update from Pleroma
        pleroma_posts_url = pleroma_base_url + '/api/v1/accounts/' + user['username'] + '/statuses'
        response = requests.get(pleroma_posts_url, headers=header_pleroma)
        posts = json.loads(response.text)
        date_pleroma = datetime.strftime(datetime.strptime(posts[0]['created_at'], '%Y-%m-%dT%H:%M:%S.000Z'),
                                         '%Y-%m-%d %H:%M:%S')

        # Get info from Twitter
        twitter_user_url = twitter_base_url + '/users/show.json?screen_name=' + user['username']
        response = requests.get(twitter_user_url, headers=header_twitter)
        user_twitter = json.loads(response.text)
        # Limit to 50 last tweets - just to make a bit easier and faster to process given how often it is pulled
        twitter_status_url = twitter_base_url + '/statuses/user_timeline.json?screen_name=' + user['username'] + \
                          '&count=50&include_rts=true'
        response = requests.get(twitter_status_url, headers=header_twitter)
        tweets = json.loads(response.text)
        # Put oldest first to iterate them and post them in order
        tweets.reverse()

        tweets_to_post = []
        # Get rid of old tweets
        for tweet in tweets:
            created_at = tweet['created_at']
            date_twitter = datetime.strftime(datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y'),
                                             '%Y-%m-%d %H:%M:%S')
            if date_twitter > date_pleroma:
                tweets_to_post.append(tweet)
        print('tweets:', tweets_to_post)
        for tweet in tweets_to_post:
            id = tweet['id_str']
            try:
                # In a RT this field includes a link to the original status
                # The status is always truncated so this is a more sane option in RTs
                text = tweet['retweeted_status']['text']
            except KeyError:
                text = tweet['text']
                pass
            try:
                media = []
                for item in tweet['entities']['media']:
                    media.append(item)
            except KeyError:
                pass
            # Create folder to store attachments related to the tweet ID
            if not os.path.isdir(os.path.join(tweets_temp_path, id)):
                os.mkdir(os.path.join(tweets_temp_path, id))
            for idx, item in media:
                response = requests.get(item['media_url'], stream=True)
                response.raw.decode_content = True
                
                with open(os.path.join(tweets_temp_path, id, idx), 'wb') as outfile:
                    shutil.copyfileobj(response.raw, outfile)

            # Post to Pleroma
            pleroma_post_url = pleroma_base_url + '/api/v1/statuses'
            # TODO: Implement upload and update of media
            # https://docs.joinmastodon.org/methods/statuses/media/
            # media_ids must be a tuple
            signature = '\n\n 🐦🔗: ' + twitter_url + '/status/' + id
            text = text + signature

            data = {"status": text, "sensitive": "true", "visibility": "unlisted", "media_ids": None}
            response = requests.post(pleroma_post_url, data, headers=header_pleroma)
            print(response.text)  

        """
        Update user info in Pleroma
        """
        if not arg == "noProfile":
            base_desc = '🤖 BEEP BOOP 🤖 \n I\'m a bot that mirrors ' + user['username'] + \
                        ' Twitter\'s account. \n Any issues please contact @robertoszek \n \n '
            description = base_desc + user_twitter['description']

            # Get the biggest resolution for the profile picture (400x400) instead of 'normal'
            profile_img_big = re.sub(r"normal", "400x400", user_twitter['profile_image_url'])
            response = requests.get(profile_img_big, stream=True)
            response.raw.decode_content = True
            with open(avatar_path, 'wb') as outfile:
                shutil.copyfileobj(response.raw, outfile)

            response = requests.get(user_twitter['profile_banner_url'], stream=True)
            response.raw.decode_content = True
            with open(header_path, 'wb') as outfile:
                shutil.copyfileobj(response.raw, outfile)

            # Set it on Pleroma
            cred_url = pleroma_base_url + '/api/v1/accounts/update_credentials'
            fields = [(":googlebird: Birdsite", twitter_url),
                      ("Status", "Text-only :blobcry: 2.0.50-develop broke it somehow"),
                      ("Source", "https://github.com/yogthos/mastodon-bot")]
            data = {"note": description, "avatar": avatar_path, "header": header_path, "display_name": user_twitter['name']}
            fields_attributes = []
            if len(fields) > 4:
                raise Exception("Maximum number of fields is 4. Exiting...")
            for idx, (field_name, field_value) in enumerate(fields):
                data['fields_attributes[' + str(idx) + '][name]'] = field_name
                data['fields_attributes[' + str(idx) + '][value]'] = field_value

            avatar = open(avatar_path, 'rb')
            avatar_mime_type = guess_type(avatar_path)
            timestamp = str(datetime.now().timestamp())
            avatar_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(avatar_mime_type)

            header = open(header_path, 'rb')
            header_mime_type = guess_type(header_path)
            header_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(header_mime_type)

            files = {"avatar": (avatar_file_name, avatar, avatar_mime_type),
                     "header": (header_file_name, header, header_mime_type)}
            response = requests.patch(cred_url, data, headers=header_pleroma, files=files)
            print(response)  # for debugging
        # Clean-up
        shutil.rmtree('tweets')


if __name__ == '__main__':
    main()
