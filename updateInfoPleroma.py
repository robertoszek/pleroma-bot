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
import yaml

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


class User(object):
    # TODO: Implement functions, move code from main when it applies
    def __init__(self, user_cfg, cfg):
        self.username = user_cfg['username']
        self.token = user_cfg['token']
        self.signature = user_cfg['signature']
        self.support_account = user_cfg['support_account']
        self.fields = []
        self.twitter_description = None
        self.bio_text = self.replace_vars_in_str(str(user_cfg['bio_text']))
        self.twitter_token = cfg['twitter_token']
        self.pleroma_base_url = cfg['pleroma_url']
        self.twitter_base_url = cfg['twitter_url']
        # Auth
        self.header_pleroma = {"Authorization": "Bearer " + self.token}
        self.header_twitter = {"Authorization": "Bearer " + self.twitter_token}
        self.tweets = None
        self.last_post_pleroma = None
        # Filesystem
        script_path = os.path.dirname(sys.argv[0])
        self.base_path = os.path.abspath(script_path)
        self.users_path = os.path.join(self.base_path, 'users')
        self.user_path = os.path.join(self.users_path, self.username)
        self.tweets_temp_path = os.path.join(self.user_path, 'tweets')
        self.avatar_path = os.path.join(self.user_path, 'profile.jpg')
        self.header_path = os.path.join(self.user_path, 'banner.jpg')
        if not os.path.isdir(self.users_path):
            os.mkdir(self.users_path)
        if not os.path.isdir(self.user_path):
            os.mkdir(self.user_path)
        if not os.path.isdir(self.tweets_temp_path):
            os.mkdir(self.tweets_temp_path)
        # self.get_last_pleroma_post()
        # self.get_tweets()
        # self.post_pleroma()
        return

    def replace_vars_in_str(self, text: str, var_name: str = None) -> str:
        """Returns a string with "{{ var_name }}" replaced with var_name's value
        If no 'var_name' is provided, locals() (or self if it's an object method)
        will be used and all variables found in locals() (or object attributes)
        will be replaced with their values.

        :param text: String to be parsed, replacing "{{ var_name }}" with var_name's value. Multiple occurrences are
                     supported.
        :type text: str
        :param var_name: Name of the variable to be replace. Multiple occurrences are supported. If not provided,
               locals() will be used and all variables will be replaced with their values.
        :type var_name: str

        :returns: A string with {{ var_name }} replaced with var_name's value.
        :rtype: str
        """
        # Jinja-style string replacement i.e. vars encapsulated in {{ and }}
        if var_name is not None:
            matching_pattern = r'(?<=\{{)( ' + var_name + r' )(?=\}})'
            matches = re.findall(matching_pattern, text)
        else:
            matches = re.findall(r'(?<={{)(.*?)(?=}})', text)
        for match in matches:
            pattern = r'{{ ' + match.strip() + ' }}'
            # This other way only works if the var is inside the function (same scope)
            # value = locals()['self.' + match.strip()]
            value = getattr(self, match.strip())
            text = re.sub(pattern, value, text)
        return text

    def _get_tweets(self):
        # Private method
        # Actually get the tweets here
        return

    def get_tweets(self):
        # Getter
        return self.tweets

    def get_date_last_pleroma_post(self):
        pleroma_posts_url = self.pleroma_base_url + '/api/v1/accounts/' + self.username + '/statuses'
        response = requests.get(pleroma_posts_url, headers=self.header_pleroma)
        posts = json.loads(response.text)
        date_pleroma = datetime.strftime(datetime.strptime(posts[0]['created_at'], '%Y-%m-%dT%H:%M:%S.000Z'),
                                         '%Y-%m-%d %H:%M:%S')
        return date_pleroma

    def update_pleroma(self):
        return


def guess_type(media_file):
    mime_type = None
    try:
        mime_type = magic.from_file(media_file, mime=True)
    except AttributeError:
        mime_type = mimetypes.guess_type(media_file)[0]
    return mime_type


def random_string(length: int) -> str:
    """Returns a string of random characters of length 'length'
    :param length: How long the string to return must be
    :type length: int
    
    :returns: an alpha-numerical string of specified length with random characters
    :rtype: str
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def main():
    # TODO: Refactor main function and split it up in smaller pieces
    # TODO: Clean up usercred.secret and twittercred.secret references
    script_path = os.path.dirname(sys.argv[0])
    base_path = os.path.abspath(script_path)
    with open('config.yml', 'r') as stream:
        config = yaml.safe_load(stream)
    user_dict = config['users']

    pleroma_base_url = config['pleroma_url']
    twitter_base_url = config['twitter_url']

    # Twitter bearer token
    twitter_token = config['twitter_token']

    for user in user_dict:
        user_obj = User(user, config)
        twitter_url = "http://nitter.net/" + user['username']
        # Set up files structure
        users_path = os.path.join(base_path, 'users')
        user_path = os.path.join(users_path, user['username'])
        tweets_temp_path = os.path.join(user_path, 'tweets')
        avatar_path = os.path.join(user_path, 'profile.jpg')
        header_path = os.path.join(user_path, 'banner.jpg')

        if not os.path.isdir(users_path):
            os.mkdir(users_path)
        if not os.path.isdir(user_path):
            os.mkdir(user_path)
        if not os.path.isdir(tweets_temp_path):
            os.mkdir(tweets_temp_path)
        # Auth
        header_pleroma = {"Authorization": "Bearer " + user['token']}
        header_twitter = {"Authorization": "Bearer " + twitter_token}

        """
        Compare and post only new tweets to Pleroma
        """

        # Get last update from Pleroma
        date_pleroma = user_obj.get_date_last_pleroma_post()
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
            tweet_id = tweet['id_str']
            text = tweet['text']
            media = []
            try:
                for item in tweet['entities']['media']:
                    media.append(item)
            except KeyError:
                pass
            # Create folder to store attachments related to the tweet ID
            if not os.path.isdir(os.path.join(tweets_temp_path, tweet_id)):
                os.mkdir(os.path.join(tweets_temp_path, tweet_id))
            print(enumerate(media))
            # TODO: Implement download of media. Make it optional
            """
            for idx, (item) in media:
                response = requests.get(item['media_url'], stream=True)
                response.raw.decode_content = True
                
                with open(os.path.join(tweets_temp_path, id, idx), 'wb') as outfile:
                    shutil.copyfileobj(response.raw, outfile)
            """
            # Post to Pleroma
            pleroma_post_url = pleroma_base_url + '/api/v1/statuses'
            # TODO: Implement upload and update of media
            # https://docs.joinmastodon.org/methods/statuses/media/
            # media_ids must be a tuple

            # TODO: make signature optional based on user['signature'] bool
            signature = '\n\n 🐦🔗: ' + twitter_url + '/status/' + tweet_id
            text = text + signature

            data = {"status": text, "sensitive": "true", "visibility": "unlisted", "media_ids": None}
            response = requests.post(pleroma_post_url, data, headers=header_pleroma)
            print(response)

        """
        Update user info in Pleroma
        """
        # TODO: Move this to a separate function
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
            data = {"note": description, "avatar": avatar_path, "header": header_path,
                    "display_name": user_twitter['name']}
            fields_attributes = []
            if len(fields) > 4:
                raise Exception("Maximum number of fields is 4. Exiting...")
            for idx, (field_name, field_value) in enumerate(fields):
                data['fields_attributes[' + str(idx) + '][name]'] = field_name
                data['fields_attributes[' + str(idx) + '][value]'] = field_value

            avatar = open(avatar_path, 'rb')
            avatar_mime_type = guess_type(avatar_path)
            timestamp = str(datetime.now().timestamp())
            avatar_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(
                avatar_mime_type)

            header = open(header_path, 'rb')
            header_mime_type = guess_type(header_path)
            header_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(
                header_mime_type)

            files = {"avatar": (avatar_file_name, avatar, avatar_mime_type),
                     "header": (header_file_name, header, header_mime_type)}
            response = requests.patch(cred_url, data, headers=header_pleroma, files=files)
            print(response)  # for debugging
        # Clean-up
        shutil.rmtree(tweets_temp_path)


if __name__ == '__main__':
    main()
