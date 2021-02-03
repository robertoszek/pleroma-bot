#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2021 Roberto Chamorro / project contributors
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
import logging
import argparse

from requests_oauthlib import OAuth1

from . import logger
from .__init__ import __version__


class User(object):
    from ._twitter import get_tweets
    from ._twitter import _get_tweets
    from ._twitter import _get_tweets_v2
    from ._twitter import _get_twitter_info

    from ._pin import pin_pleroma
    from ._pin import unpin_pleroma
    from ._pin import get_pinned_tweet
    from ._pin import _get_pinned_tweet_id

    from ._pleroma import post_pleroma
    from ._pleroma import update_pleroma
    from ._pleroma import get_date_last_pleroma_post

    from ._utils import force_date
    from ._utils import guess_type
    from ._utils import check_pinned
    from ._utils import random_string
    from ._utils import _get_instance_info
    from ._utils import replace_vars_in_str

    from ._processing import process_tweets

    from ._processing import _expand_urls
    from ._processing import _get_media_url
    from ._processing import _process_polls
    from ._processing import _replace_nitter
    from ._processing import _download_media
    from ._processing import _replace_mentions
    from ._processing import _get_best_bitrate_video

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
        self.first_time = False
        try:
            self.fields = self.replace_vars_in_str(str(user_cfg["fields"]))
            self.fields = eval(self.fields)
        except KeyError:
            self.fields = []
        self.bio_text = self.replace_vars_in_str(str(user_cfg["bio_text"]))
        # Auth
        self.header_pleroma = {"Authorization": f"Bearer {self.pleroma_token}"}
        self.header_twitter = {"Authorization": f"Bearer {self.twitter_token}"}
        try:
            if all([
                self.consumer_key,
                self.consumer_secret,
                self.access_token_key,
                self.access_token_secret
            ]):
                self.auth = OAuth1(
                    self.consumer_key,
                    self.consumer_secret,
                    self.access_token_key,
                    self.access_token_secret
                )
        except AttributeError:
            logger.debug(
                "Some or all OAuth 1.0a tokens missing, "
                "falling back to application-only authentication"
            )
            self.auth = None

        self.tweets = None
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


def get_args(sysargs):
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Bot for mirroring one or multiple Twitter accounts "
            "in Pleroma/Mastodon."
        )
    )

    parser.add_argument(
        "-n",
        "--noProfile",
        required=False,
        action="store_true",
        help=(
            "skips Fediverse profile update (no background "
            "image, profile image, bio text, etc.)"
        ),
    )

    parser.add_argument(
        "--forceDate",
        nargs="?",
        required=False,
        action="store",
        const="all",
        help=(
            "forces the tweet retrieval to start from a "
            "specific date. The twitter_username value "
            "(FORCEDATE) can be supplied to only force it for "
            "that particular user in the config"
        ),
    )

    parser.add_argument(
        "-s",
        "--skipChecks",
        required=False,
        action="store_true",
        help=("skips first run checks"),
    )

    parser.add_argument("--verbose", "-v", action="count", default=0)

    parser.add_argument(
        "--version", action="version", version=f"{__version__}"
    )

    args, extra = parser.parse_known_args(sysargs)
    return args


def main():
    # Convert legacy flag to proper flag format
    mangle_args = "noProfile"
    arguments = [
        "--" + arg if arg in mangle_args else arg for arg in sys.argv[1:]
    ]
    args = get_args(sysargs=arguments)

    if args.verbose > 0:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    try:
        base_path = os.getcwd()
        with open(os.path.join(base_path, "config.yml"), "r") as stream:
            config = yaml.safe_load(stream)
        user_dict = config["users"]
        users_path = os.path.join(base_path, "users")
        # TODO: Merge tweets of multiple accounts and order them by date
        for user_item in user_dict[:]:
            user_item["skip_pin"] = False
            if isinstance(user_item["twitter_username"], list):
                warn_msg = (
                    "Multiple twitter users for one Fediverse account, "
                    "skipping profile and pinned tweet."
                )
                logger.warning(warn_msg)
                user_item["skip_pin"] = True
                for twitter_user in user_item["twitter_username"]:
                    new_user = dict(user_item)
                    new_user["twitter_username"] = twitter_user
                    user_dict.append(new_user)
                user_dict.remove(user_item)

        for user_item in user_dict:
            first_time = False
            logger.info("======================================")
            logger.info(f'Processing user:\t{user_item["pleroma_username"]}')
            user_path = os.path.join(users_path, user_item["twitter_username"])

            if not os.path.exists(user_path):
                first_time_msg = (
                    "It seems like pleroma-bot is running for the "
                    "first time for this user"
                )
                logger.info(first_time_msg)
                first_time = True
            user = User(user_item, config)
            if first_time and not args.skipChecks:
                user.first_time = True
            if (
                (args.forceDate and args.forceDate == user.twitter_username)
                or args.forceDate == "all"
                or user.first_time
            ) and not args.skipChecks:
                date_pleroma = user.force_date()
            else:
                date_pleroma = user.get_date_last_pleroma_post()
            tweets = user.get_tweets(start_time=date_pleroma)
            logger.debug(f"tweets: \t {tweets}")

            if 'meta' not in tweets:
                error_msg = (
                    "Unable to retrieve tweets. Is the account protected?"
                    " If so, you need to provide the following OAuth 1.0a"
                    " fields in the user config:\n - consumer_key \n "
                    "- consumer_secret \n - access_token_key \n "
                    "- access_token_secret"
                )
                logger.error(error_msg)

            if tweets["meta"]["result_count"] > 0:
                logger.info(f"tweet count: \t {len(tweets['data'])}")
                # Put oldest first to iterate them and post them in order
                tweets["data"].reverse()
                tweets_to_post = user.process_tweets(tweets)
                logger.debug(f"tweets_processed: \t {tweets_to_post['data']}")
                tweet_counter = 0
                for tweet in tweets_to_post["data"]:
                    tweet_counter += 1
                    logger.info(
                        f"({tweet_counter}/{len(tweets_to_post['data'])})"
                    )
                    user.post_pleroma(
                        (tweet["id"], tweet["text"]),
                        tweet["polls"],
                        tweet["possibly_sensitive"],
                    )
                    time.sleep(0.5)
            if not user.skip_pin:
                user.check_pinned()

            if not args.noProfile:
                if user.skip_pin:
                    logger.warning(
                        "Multiple twitter users, not updating profile"
                    )
                else:
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
