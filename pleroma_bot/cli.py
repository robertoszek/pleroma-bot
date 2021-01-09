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
# The above copyright notice and this permission notice shall be included in
# all
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
import time

import yaml
import shutil

from datetime import datetime

from . import logger


class User(object):
    from ._twitter import get_tweets
    from ._twitter import _get_tweets
    from ._twitter import _get_twitter_info

    from ._pin import pin_pleroma
    from ._pin import unpin_pleroma
    from ._pin import get_pinned_tweet
    from ._pin import _get_pinned_tweet_id

    from ._pleroma import post_pleroma
    from ._pleroma import update_pleroma
    from ._pleroma import get_date_last_pleroma_post

    from ._utils import guess_type
    from ._utils import check_pinned
    from ._utils import random_string
    from ._utils import process_tweets
    from ._utils import replace_vars_in_str

    from ._utils import _expand_urls
    from ._utils import _get_media_url
    from ._utils import _process_polls
    from ._utils import _replace_nitter
    from ._utils import _download_media
    from ._utils import _replace_mentions
    from ._utils import _get_instance_info
    from ._utils import _get_best_bitrate_video

    def __init__(self, user_cfg: dict, cfg: dict):
        self.twitter_token = cfg["twitter_token"]
        self.signature = ""
        self.media_upload = False
        self.support_account = None
        # iterate attrs defined in config
        for attribute in user_cfg:
            self.__setattr__(attribute, user_cfg[attribute])
        self.twitter_url = f"http://twitter.com/{self.twitter_username}"
        try:
            if not hasattr(self, "max_tweets"):
                self.max_tweets = cfg["max_tweets"]
        except (KeyError, AttributeError):
            # Limit to 50 last tweets - just to make a bit easier and faster
            # to process given how often it is pulled
            self.max_tweets = 50
            pass
        try:
            if not hasattr(self, "visibility"):
                self.visibility = cfg["visibility"]
        except (KeyError, AttributeError):
            self.visibility = "unlisted"
            pass
        visibility_valid = ("public", "unlisted", "private", "direct")
        if self.visibility not in visibility_valid:
            raise KeyError(
                "Visibility not supported! Values allowed are: public, "
                "unlisted, private and direct"
            )
        try:
            if not hasattr(self, "sensitive"):
                self.sensitive = cfg["sensitive"]
        except (KeyError, AttributeError):
            pass
        if hasattr(self, "rich_text"):
            if self.rich_text:
                self.content_type = "text/markdown"
        try:
            if not hasattr(self, "pleroma_base_url"):
                self.pleroma_base_url = cfg["pleroma_base_url"]
        except KeyError:
            raise KeyError(
                "No Pleroma URL defined in config! [pleroma_base_url]"
            )
        try:
            if not hasattr(self, "twitter_base_url"):
                self.twitter_base_url = cfg["twitter_base_url"]
        except KeyError:
            self.twitter_base_url = "https://api.twitter.com/1.1"
            pass
        try:
            if not hasattr(self, "twitter_base_url_v2"):
                self.twitter_base_url = cfg["twitter_base_url_v2"]
        except KeyError:
            self.twitter_base_url_v2 = "https://api.twitter.com/2"
            pass
        try:
            if not hasattr(self, "nitter_base_url"):
                self.nitter_base_url = cfg["nitter_base_url"]
        except KeyError:
            self.nitter_base_url = "https://nitter.net"
            pass
        if not hasattr(self, "nitter"):
            try:
                if cfg["nitter"]:
                    self.twitter_url = (
                        f"{self.nitter_base_url}/{self.twitter_username}"
                    )
            except KeyError:
                pass
        else:
            if self.nitter:
                self.twitter_url = (
                    f"{self.nitter_base_url}/{self.twitter_username}"
                )
        try:
            if not hasattr(self, "include_rts"):
                self.include_rts = cfg["include_rts"]
        except (KeyError, AttributeError):
            self.include_rts = True
            pass
        try:
            if not hasattr(self, "include_replies"):
                self.include_rts = cfg["include_replies"]
        except (KeyError, AttributeError):
            self.include_replies = True
            pass
        self.profile_image_url = None
        self.profile_banner_url = None
        self.display_name = None
        try:
            self.fields = self.replace_vars_in_str(str(user_cfg["fields"]))
            self.fields = eval(self.fields)
        except KeyError:
            self.fields = []
        self.bio_text = self.replace_vars_in_str(str(user_cfg["bio_text"]))
        # Auth
        self.header_pleroma = {"Authorization": f"Bearer {self.pleroma_token}"}
        self.header_twitter = {"Authorization": f"Bearer {self.twitter_token}"}
        self.tweets = self._get_tweets("v2")
        self.pinned_tweet_id = self._get_pinned_tweet_id()
        self.last_post_pleroma = None
        # Filesystem
        self.base_path = os.getcwd()
        self.users_path = os.path.join(self.base_path, "users")
        self.user_path = os.path.join(self.users_path, self.twitter_username)
        self.tweets_temp_path = os.path.join(self.user_path, "tweets")
        self.avatar_path = os.path.join(self.user_path, "profile.jpg")
        self.header_path = os.path.join(self.user_path, "banner.jpg")
        os.makedirs(self.users_path, exist_ok=True)
        os.makedirs(self.user_path, exist_ok=True)
        os.makedirs(self.tweets_temp_path, exist_ok=True)
        # Get Twitter info on instance creation
        self._get_twitter_info()
        self._get_instance_info()
        self.posts = None
        return


def main():
    # Parameter to choose whether to update bio, avatar and banner or not -
    # save some bandwidth
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = ""
        print(f"Usage: {sys.argv[0]} [noProfile]")

    try:
        base_path = os.getcwd()
        with open(os.path.join(base_path, "config.yml"), "r") as stream:
            config = yaml.safe_load(stream)
        user_dict = config["users"]

        for user_item in user_dict:
            logger.info("======================================")
            logger.info(f'Processing user:\t{user_item["pleroma_username"]}')
            user = User(user_item, config)
            date_pleroma = user.get_date_last_pleroma_post()
            tweets = user.get_tweets()
            if tweets["meta"]["result_count"] > 0:
                # Put oldest first to iterate them and post them in order
                tweets["data"].reverse()
                tweets_to_post = {"data": [], "includes": tweets["includes"]}
                # Get rid of old tweets
                for tweet in tweets["data"]:
                    created_at = tweet["created_at"]
                    date_twitter = datetime.strftime(
                        datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ"),
                        "%Y-%m-%d %H:%M:%S",
                    )
                    if date_twitter > date_pleroma:
                        tweets_to_post["data"].append(tweet)

                tweets_to_post = user.process_tweets(tweets_to_post)
                logger.info(f"tweets: \t {tweets_to_post['data']}")
                for tweet in tweets_to_post["data"]:
                    user.post_pleroma(
                        (tweet["id"], tweet["text"]),
                        tweet["polls"],
                        tweet["possibly_sensitive"],
                    )
                    time.sleep(2)

            user.check_pinned()

            if not arg == "noProfile":
                user.update_pleroma()
            # Clean-up
            shutil.rmtree(user.tweets_temp_path)
    except Exception:
        logger.error("Exception occurred", exc_info=True)
        return 1

    return 0


def init():
    if __name__ == "__main__":
        sys.exit(main())


init()
