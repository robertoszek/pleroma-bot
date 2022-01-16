#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2022 Roberto Chamorro / project contributors
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
import multiprocessing as mp

from requests_oauthlib import OAuth1
from requests.structures import CaseInsensitiveDict

from .i18n import _
from . import logger
from .__init__ import __version__
from ._utils import process_parallel, Locker, process_archive


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
    from ._processing import _replace_url
    from ._processing import _get_media_url
    from ._processing import _process_polls
    from ._processing import _download_media
    from ._processing import _replace_mentions
    from ._processing import _get_best_bitrate_video

    def __init__(self, user_cfg: dict, cfg: dict, base_path: str):
        self.posts = None
        self.tweets = None
        self.first_time = False
        self.display_name = {}
        self.last_post_pleroma = None
        self.profile_image_url = {}
        self.profile_banner_url = {}
        self.t_user_tweets = {}
        self.twitter_ids = {}
        valid_visibility = ("public", "unlisted", "private", "direct")
        default_cfg_attributes = {
            "twitter_base_url": "https://api.twitter.com/1.1",
            "twitter_base_url_v2": "https://api.twitter.com/2",
            "nitter_base_url": "https://nitter.net",
            "pleroma_base_url": None,
            "nitter": False,
            "twitter_token": None,
            "signature": False,
            "media_upload": True,
            "sensitive": False,
            "max_tweets": 50,
            "delay_post": 0.5,
            "visibility": "unlisted",
            "hashtags": [],
            "tweet_ids": [],
            "rich_text": False,
            "twitter_bio": True,
            "include_rts": True,
            "include_replies": True,
            "consumer_key": None,
            "consumer_secret": None,
            "access_token_key": None,
            "access_token_secret": None,
            "original_date": False,
            "original_date_format": "%Y-%m-%d %H:%M",
            "bio_text": "",
            "keep_media_links": False,
            "fields": [],
            "invidious": False,
            "invidious_base_url": "https://yewtu.be/",
            "archive": None,
        }
        # iterate attrs defined in config
        for attribute in default_cfg_attributes:
            if attribute in cfg:
                self.__setattr__(attribute, cfg[attribute])
            if not hasattr(self, attribute):
                self.__setattr__(attribute, default_cfg_attributes[attribute])
        for user_attribute in user_cfg:
            self.__setattr__(user_attribute, user_cfg[user_attribute])

        t_users = self.twitter_username
        t_users_list = isinstance(t_users, list)
        t_users = [t_users] if not t_users_list else t_users
        self.twitter_username = t_users

        twitter_url = (
            self.nitter_base_url if self.nitter else "http://twitter.com"
        )

        if self.rich_text:
            self.content_type = "text/markdown"
        if not self.pleroma_base_url:
            raise KeyError(
                _("No Pleroma URL defined in config! [pleroma_base_url]")
            )
        if self.visibility not in valid_visibility:
            raise KeyError(
                _("Visibility not supported! Values allowed are: {}").format(
                    ", ".join(valid_visibility)
                )
            )

        bio_text = self.replace_vars_in_str(str(self.bio_text))
        self.bio_text = {"_generic_bio_text": bio_text}

        # Auth
        self.header_pleroma = {"Authorization": f"Bearer {self.pleroma_token}"}
        self.header_twitter = {"Authorization": f"Bearer {self.twitter_token}"}

        if all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.access_token_key,
                self.access_token_secret,
            ]
        ):
            self.auth = OAuth1(
                self.consumer_key,
                self.consumer_secret,
                self.access_token_key,
                self.access_token_secret,
            )
        else:
            self.auth = None
            logger.debug(
                _(
                    "Some or all OAuth 1.0a tokens missing, "
                    "falling back to application-only authentication"
                )
            )

        self.twitter_url = CaseInsensitiveDict()
        for t_user in t_users:
            self.twitter_url[t_user] = f"{twitter_url}/{t_user}"
        self.pinned_tweet_id = self._get_pinned_tweet_id()
        self.fields = self.replace_vars_in_str(str(self.fields))
        self.fields = eval(self.fields)
        self.base_path = base_path
        self.users_path = os.path.join(self.base_path, "users")
        self.tweets_temp_path = os.path.join(self.base_path, "tweets")
        self.user_path = {}
        self.avatar_path = {}
        self.header_path = {}
        for t_user in t_users:
            self.user_path[t_user] = os.path.join(self.users_path, t_user)
            t_path = self.user_path[t_user]
            self.avatar_path[t_user] = os.path.join(t_path, "profile.jpg")
            self.header_path[t_user] = os.path.join(t_path, "banner.jpg")
        os.makedirs(self.users_path, exist_ok=True)
        os.makedirs(self.tweets_temp_path, exist_ok=True)
        for t_user in t_users:
            os.makedirs(self.user_path[t_user], exist_ok=True)
        # Get Twitter info on instance creation
        self._get_twitter_info()
        self._get_instance_info()

        return


def get_args(sysargs):
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(
        description=(
            _(
                "Bot for mirroring one or multiple Twitter accounts "
                "in Pleroma/Mastodon."
            )
        )
    )

    parser.add_argument(
        "-c",
        "--config",
        required=False,
        action="store",
        help=(
            _(
                "path of config file (config.yml) to use and parse. If not"
                " specified, it will try to find it in the current working "
                "directory."
            )
        ),
    )

    parser.add_argument(
        "-l",
        "--log",
        required=False,
        action="store",
        help=(
            _(
                "path of log file (error.log) to create. If not"
                " specified, it will try to store it at your config file path"
            )
        ),
    )

    parser.add_argument(
        "-n",
        "--noProfile",
        required=False,
        action="store_true",
        help=(
            _(
                "skips Fediverse profile update (no background "
                "image, profile image, bio text, etc.)"
            )
        ),
    )

    parser.add_argument(
        "--forceDate",
        nargs="?",
        required=False,
        action="store",
        const="all",
        help=(
            _(
                "forces the tweet retrieval to start from a "
                "specific date. The twitter_username value "
                "(FORCEDATE) can be supplied to only force it for "
                "that particular user in the config"
            )
        ),
    )

    parser.add_argument(
        "-s",
        "--skipChecks",
        required=False,
        action="store_true",
        help=(_("skips first run checks")),
    )

    parser.add_argument(
        "-a",
        "--archive",
        required=False,
        action="store",
        help=(
            _(
                "path of the Twitter archive file (zip) to use for posting "
                "tweets."
            )
        ),
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
        logging.debug(_("Debug logging enabled"))

    try:
        base_path = os.getcwd()
        if args.config:
            config_path = args.config
            base_path, cfg_file = os.path.split(os.path.abspath(config_path))
        else:
            config_path = os.path.join(base_path, "config.yml")
        tweets_temp_path = os.path.join(base_path, "tweets")
        logger.info(_("config path: {}").format(config_path))
        logger.info(_("tweets temp folder: {}").format(tweets_temp_path))
        # TODO: Add config generator wizard if config file is not found?
        #  create a minimal config asking the user for the values
        with open(config_path, "r") as stream:
            config = yaml.safe_load(stream)
        user_dict = config["users"]
        users_path = os.path.join(base_path, "users")
        for user_item in user_dict[:]:
            user_item["skip_pin"] = False
            t_users = user_item["twitter_username"]
            t_user_list = isinstance(t_users, list)
            t_users = t_users if t_user_list else [t_users]
            if len(t_users) > 1:
                warn_msg = _(
                    "Multiple twitter users for one Fediverse account, "
                    "skipping profile and pinned tweet."
                )
                logger.warning(warn_msg)
                user_item["skip_pin"] = True

        for user_item in user_dict:
            first_time = False
            logger.info("======================================")
            logger.info(
                _("Processing user:\t{}").format(user_item["pleroma_username"])
            )
            t_users = user_item["twitter_username"]
            t_user_list = isinstance(t_users, list)
            t_users = t_users if t_user_list else [t_users]
            for t_user in t_users:
                user_path = os.path.join(users_path, t_user)

                if not os.path.exists(user_path):
                    first_time_msg = _(
                        "It seems like pleroma-bot is running for the "
                        "first time for this Twitter user: {}"
                    ).format(t_user)
                    logger.info(first_time_msg)
                    first_time = True
            user = User(user_item, config, base_path)
            if args.archive:
                user.archive = args.archive
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

            if user.tweet_ids:
                tweets = {
                    "data": [],
                    "includes": {},
                    "meta": {"result_count": len(user.tweet_ids)},
                }
                user.result_count = len(user.tweet_ids)
                includes = ["users", "tweets", "media", "polls"]
                for include in includes:
                    try:
                        _include = tweets["includes"][include]
                    except KeyError:
                        tweets["includes"].update({include: []})
                for tweet_id in user.tweet_ids:
                    next_tweet = user._get_tweets("v2", tweet_id=tweet_id)
                    includes = ["users", "tweets", "media", "polls"]
                    for include in includes:
                        try:
                            _include = next_tweet["includes"][include]
                            _include = _include
                        except KeyError:
                            next_tweet["includes"].update({include: []})
                    tweets["data"].append(next_tweet["data"])
                    for user_tweet in next_tweet["includes"]["users"]:
                        tweets["includes"]["users"].append(user_tweet)
                    for tweet_include in next_tweet["includes"]["tweets"]:
                        tweets["includes"]["tweets"].append(tweet_include)
                    for media in next_tweet["includes"]["media"]:
                        tweets["includes"]["media"].append(media)
                    for poll in next_tweet["includes"]["polls"]:
                        tweets["includes"]["polls"].append(poll)
            elif args.archive:
                tweets = process_archive(args.archive, start_time=date_pleroma)
                user.result_count = len(tweets["data"])
            else:
                tweets = user.get_tweets(start_time=date_pleroma)
            logger.debug(f"tweets: \t {tweets}")

            if "meta" not in tweets:
                error_msg = _(
                    "Unable to retrieve tweets. Is the account protected?"
                    " If so, you need to provide the following OAuth 1.0a"
                    " fields in the user config:\n - consumer_key \n "
                    "- consumer_secret \n - access_token_key \n "
                    "- access_token_secret"
                )
                logger.error(error_msg)
            if user.result_count > 0:
                logger.info(
                    _("tweets gathered: \t {}").format(len(tweets["data"]))
                )
                # Put oldest first to iterate them and post them in order
                tweets["data"].reverse()
                cores = mp.cpu_count()
                threads = round(cores / 2 if cores > 4 else 4)
                tweets_to_post = process_parallel(tweets, user, threads)
                logger.info(
                    _("tweets to post: \t {}").format(
                        len(tweets_to_post['data'])
                    )
                )
                logger.debug(f"tweets_processed: \t {tweets_to_post['data']}")
                tweet_counter = 0
                for tweet in tweets_to_post["data"]:
                    tweet_counter += 1
                    logger.info(
                        f"({tweet_counter}/{len(tweets_to_post['data'])})"
                    )
                    user.post_pleroma(
                        (tweet["id"], tweet["text"], tweet["created_at"]),
                        tweet["polls"],
                        tweet["possibly_sensitive"],
                    )

                    time.sleep(user.delay_post)
            if not user.skip_pin:
                user.check_pinned()

            if not args.noProfile:
                if user.skip_pin:
                    logger.warning(
                        _("Multiple twitter users, not updating profile")
                    )
                else:
                    user.update_pleroma()
            # Clean-up
            shutil.rmtree(user.tweets_temp_path)
    except Exception:
        logger.error(_("Exception occurred"), exc_info=True)
        return 1

    return 0


def init():
    # Convert legacy flag to proper flag format
    mangle_args = "noProfile"
    arguments = [
        "--" + arg if arg in mangle_args else arg for arg in sys.argv[1:]
    ]
    args = get_args(sysargs=arguments)
    if args.log:
        log_path = args.log
    elif args.config:
        base_path, cfg_file = os.path.split(os.path.abspath(args.config))
        log_path = os.path.join(base_path, "error.log")
    else:
        log_path = os.path.join(os.getcwd(), "error.log")
    f_handler = logging.FileHandler(log_path)
    f_handler.setLevel(logging.ERROR)
    f_format = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s: %(message)s"
    )
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    if __name__ == "__main__":
        with Locker():
            sys.exit(main())


init()
