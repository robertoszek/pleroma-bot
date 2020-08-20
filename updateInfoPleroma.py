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

# TODO: Write tests
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
    def __init__(self, user_cfg: dict, cfg: dict):
        # TODO: Figure out a cleaner way of doing this config parsing without so many exception handlers
        self.username = user_cfg['username']
        self.token = user_cfg['token']
        self.signature = ""
        # Limit to 50 last tweets - just to make a bit easier and faster to process given how often it is pulled
        self.max_tweets = 50
        try:
            self.max_tweets = cfg['max_tweets']
        except KeyError:
            pass
        try:
            self.max_tweets = user_cfg['max_tweets']
        except KeyError:
            pass
        try:
            self.signature = user_cfg['signature']
        except KeyError:
            pass
        try:
            self.support_account = user_cfg['support_account']
        except KeyError:
            self.support_account = None
        self.fields = []
        self.bio_text = self.replace_vars_in_str(str(user_cfg['bio_text']))
        self.twitter_token = cfg['twitter_token']
        self.twitter_url = "http://twitter.com/" + self.username
        try:
            self.pleroma_base_url = cfg['pleroma_url']
        except KeyError:
            pass
        try:
            self.pleroma_base_url = user_cfg['pleroma_url']
        except KeyError:
            pass
        try:
            self.twitter_base_url = cfg['twitter_url']
        except KeyError:
            pass
        try:
            self.twitter_base_url = user_cfg['twitter_url']
        except KeyError:
            pass
        try:
            if cfg['nitter']:
                self.twitter_url = "http://nitter.net/" + self.username
        except KeyError:
            pass
        self.profile_image_url = None
        self.profile_banner_url = None
        self.display_name = None
        # Auth
        self.header_pleroma = {"Authorization": "Bearer " + self.token}
        self.header_twitter = {"Authorization": "Bearer " + self.twitter_token}
        self.tweets = self._get_tweets()
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
        # Get Twitter info on instance creation
        self._get_twitter_info()
        return

    def _get_twitter_info(self):
        """Updates User object attributes with current Twitter info

        This includes:

        * Bio text
        * Profile image url
        * Banner image url
        * Screen name

        :return: None
        """
        twitter_user_url = self.twitter_base_url + '/users/show.json?screen_name=' + self.username
        response = requests.get(twitter_user_url, headers=self.header_twitter)
        user_twitter = json.loads(response.text)
        self.bio_text = self.bio_text + user_twitter['description']
        self.profile_image_url = user_twitter['profile_image_url']
        self.profile_banner_url = user_twitter['profile_banner_url']
        self.display_name = user_twitter['name']
        return

    def _get_tweets(self):
        """Gathers last 'max_tweets' tweets from the user and returns them as an dict

        :returns: last 'max_tweets' tweets
        :rtype: dict
        """
        twitter_status_url = self.twitter_base_url + '/statuses/user_timeline.json?screen_name=' + \
                             self.username + '&count=' + str(self.max_tweets) + '&include_rts=true'
        response = requests.get(twitter_status_url, headers=self.header_twitter)
        tweets = json.loads(response.text)
        return tweets

    def get_tweets(self):
        return self.tweets

    def get_date_last_pleroma_post(self):
        """Gathers last post from the user in Pleroma and returns the date of creation.
        
        :returns: Date of last Pleroma post in '%Y-%m-%d %H:%M:%S' format
        """
        pleroma_posts_url = self.pleroma_base_url + '/api/v1/accounts/' + self.username + '/statuses'
        response = requests.get(pleroma_posts_url, headers=self.header_pleroma)
        posts = json.loads(response.text)
        date_pleroma = datetime.strftime(datetime.strptime(posts[0]['created_at'], '%Y-%m-%dT%H:%M:%S.000Z'),
                                         '%Y-%m-%d %H:%M:%S')
        return date_pleroma

    def post_pleroma(self, tweet_id: str, tweet_text: str) -> None:
        """Post the given text to the Pleroma instance associated with the User object
        
        :param tweet_id: It will be used to link to the Twitter status if 'signature' is True and to find related media
        :type tweet_id: str
        :param tweet_text: Literal text to use when creating the post.
        :type tweet_text: str
        :returns: None
        """
        # TODO: resolve urls and transform twitter links to nitter links, if self.nitter 'true'
        pleroma_post_url = self.pleroma_base_url + '/api/v1/statuses'
        # TODO: Implement upload and update of media
        # https://docs.joinmastodon.org/methods/statuses/media/
        # media_ids must be a tuple

        if self.signature:
            signature = '\n\n 🐦🔗: ' + self.twitter_url + '/status/' + tweet_id
            tweet_text = tweet_text + signature

        data = {"status": tweet_text, "sensitive": "true", "visibility": "unlisted", "media_ids": None}
        response = requests.post(pleroma_post_url, data, headers=self.header_pleroma)
        print(response)

    def update_pleroma(self):
        """Update the Pleroma user info with the one retrieve from Twitter when the User object was created.
        This includes:
        
        * Profile image
        * Banner image
        * Bio text
        * Screen name
        * Additional metadata fields
        
        :returns: None 
        """
        # Get the biggest resolution for the profile picture (400x400) instead of 'normal'
        profile_img_big = re.sub(r"normal", "400x400", self.profile_image_url)
        response = requests.get(profile_img_big, stream=True)
        response.raw.decode_content = True
        with open(self.avatar_path, 'wb') as outfile:
            shutil.copyfileobj(response.raw, outfile)

        response = requests.get(self.profile_banner_url, stream=True)
        response.raw.decode_content = True
        with open(self.header_path, 'wb') as outfile:
            shutil.copyfileobj(response.raw, outfile)

        # Set it on Pleroma
        cred_url = self.pleroma_base_url + '/api/v1/accounts/update_credentials'
        fields = [(":googlebird: Birdsite", self.twitter_url),
                  ("Status", "Text-only :blobcry: 2.0.50-develop broke it somehow"),
                  ("Source", "https://github.com/yogthos/mastodon-bot")]
        data = {"note": self.bio_text, "avatar": self.avatar_path, "header": self.header_path,
                "display_name": self.display_name}
        fields_attributes = []
        if len(fields) > 4:
            raise Exception("Maximum number of fields is 4. Exiting...")
        for idx, (field_name, field_value) in enumerate(fields):
            data['fields_attributes[' + str(idx) + '][name]'] = field_name
            data['fields_attributes[' + str(idx) + '][value]'] = field_value

        avatar = open(self.avatar_path, 'rb')
        avatar_mime_type = guess_type(self.avatar_path)
        timestamp = str(datetime.now().timestamp())
        avatar_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(
            avatar_mime_type)

        header = open(self.header_path, 'rb')
        header_mime_type = guess_type(self.header_path)
        header_file_name = "pleromapyupload_" + timestamp + "_" + random_string(10) + mimetypes.guess_extension(
            header_mime_type)

        files = {"avatar": (avatar_file_name, avatar, avatar_mime_type),
                 "header": (header_file_name, header, header_mime_type)}
        response = requests.patch(cred_url, data, headers=self.header_pleroma, files=files)
        print(response)  # for debugging
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
            # Get attribute value if it's a method
            # go for locals() if not, fallback to globals()
            try:
                value = getattr(self, match.strip())
            except NameError:
                try:
                    value = locals()[match.strip()]
                except NameError:
                    value = globals()[match.strip()]
            text = re.sub(pattern, value, text)
        return text


def guess_type(media_file: str) -> str:
    """Try to guess what MIME type the given file is.

    :param media_file: The file to perform the guessing on
    :returns: the MIME type result of guessing
    :rtype: str
    """
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
    script_path = os.path.dirname(sys.argv[0])
    base_path = os.path.abspath(script_path)
    with open(os.path.join(base_path, 'config.yml'), 'r') as stream:
        config = yaml.safe_load(stream)
    user_dict = config['users']

    for user_item in user_dict:
        user = User(user_item, config)
        date_pleroma = user.get_date_last_pleroma_post()
        tweets = user.get_tweets()
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
            tweet_text = tweet['text']
            media = []
            try:
                for item in tweet['entities']['media']:
                    media.append(item)
            except KeyError:
                pass
            # Create folder to store attachments related to the tweet ID
            tweet_path = os.path.join(user.tweets_temp_path, tweet_id)
            if not os.path.isdir(tweet_path):
                os.mkdir(tweet_path)
            print(enumerate(media))
            # TODO: Implement download of media. Make it optional
            """
            for idx, (item) in media:
                response = requests.get(item['media_url'], stream=True)
                response.raw.decode_content = True
                
                with open(os.path.join(tweets_temp_path, id, idx), 'wb') as outfile:
                    shutil.copyfileobj(response.raw, outfile)
            """
            user.post_pleroma(tweet_id, tweet_text)

        if not arg == "noProfile":
            user.update_pleroma()
        # Clean-up
        shutil.rmtree(user.tweets_temp_path)


if __name__ == '__main__':
    main()
