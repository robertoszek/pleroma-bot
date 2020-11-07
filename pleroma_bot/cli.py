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

# TODO: Refactor cli.py into smaller sections
import os
import sys
import time
import string
import random
from json.decoder import JSONDecodeError

import re
import json
import yaml
import shutil
import requests
import mimetypes

from . import logger

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from datetime import datetime, timedelta

# Parameter to choose whether to update bio, avatar and banner or not - save
# some bandwidth
try:
    arg = sys.argv[1]
except IndexError:
    arg = ""
    print(f"Usage: {sys.argv[0]} [noProfile]")


class User(object):
    def __init__(self, user_cfg: dict, cfg: dict):
        self.twitter_token = cfg["twitter_token"]
        self.signature = ""
        self.media_upload = False
        self.support_account = None
        # iterate attrs defined in config
        for attribute in user_cfg:
            self.__setattr__(attribute, user_cfg[attribute])
        self.twitter_url = "http://twitter.com/" + self.twitter_username
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
        if self.visibility not in ("public", "unlisted", "private", "direct"):
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
        if not hasattr(self, "nitter"):
            try:
                if cfg["nitter"]:
                    self.twitter_url = (
                        f"http://nitter.net/" f"{self.twitter_username}"
                    )
            except KeyError:
                pass
        else:
            if self.nitter:
                self.twitter_url = "http://nitter.net/" + self.twitter_username
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
        self.header_pleroma = {"Authorization": "Bearer " + self.pleroma_token}
        self.header_twitter = {"Authorization": "Bearer " + self.twitter_token}
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
        if not os.path.isdir(self.users_path):
            os.mkdir(self.users_path)
        if not os.path.isdir(self.user_path):
            os.mkdir(self.user_path)
        if not os.path.isdir(self.tweets_temp_path):
            os.mkdir(self.tweets_temp_path)
        # Get Twitter info on instance creation
        self._get_twitter_info()
        self.posts = None
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
        twitter_user_url = (
            f"{self.twitter_base_url}"
            f"/users/show.json?screen_name="
            f"{self.twitter_username}"
        )
        response = requests.get(twitter_user_url, headers=self.header_twitter)
        if not response.ok:
            response.raise_for_status()
        user_twitter = json.loads(response.text)
        self.bio_text = self.bio_text + user_twitter["description"]
        # Check if user has profile image
        if "profile_image_url_https" in user_twitter.keys():
            self.profile_image_url = user_twitter["profile_image_url_https"]
        # Check if user has banner image
        if "profile_banner_url" in user_twitter.keys():
            self.profile_banner_url = user_twitter["profile_banner_url"]
        self.display_name = user_twitter["name"]
        return

    def _get_tweets(self, version: str, tweet_id=None):
        """Gathers last 'max_tweets' tweets from the user and returns them
        as an dict
        :param version: Twitter API version to use to retrieve the tweets
        :type version: string
        :param tweet_id: Tweet ID to retrieve
        :type tweet_id: int

        :returns: last 'max_tweets' tweets
        :rtype: dict
        """
        if version == "v1.1":
            if tweet_id:
                twitter_status_url = (
                    f"{self.twitter_base_url}/statuses/"
                    f"show.json?id={str(tweet_id)}"
                )
                response = requests.get(
                    twitter_status_url, headers=self.header_twitter
                )
                if not response.ok:
                    response.raise_for_status()
                tweet = json.loads(response.text)
                return tweet
            else:
                twitter_status_url = (
                    f"{self.twitter_base_url}"
                    f"/statuses/user_timeline.json?screen_name="
                    f"{self.twitter_username}"
                    f"&count={str(self.max_tweets)}&include_rts=true"
                )
                response = requests.get(
                    twitter_status_url, headers=self.header_twitter
                )
                if not response.ok:
                    response.raise_for_status()
                tweets = json.loads(response.text)
                return tweets
        elif version == "v2":
            params = {}
            if tweet_id:
                url = f"{self.twitter_base_url_v2}/tweets/{tweet_id}"
            else:
                url = f"{self.twitter_base_url_v2}/tweets/search/recent"
                # this only gets tweets from last week
                params.update(
                    {
                        "max_results": self.max_tweets,
                        "query": "from:" + self.twitter_username,
                    }
                )
            # Tweet number must be between 10 and 100
            if not (100 >= self.max_tweets > 10):
                raise ValueError(
                    f"max_tweets must be between 10 and 100. max_tweets: "
                    f"{self.max_tweets}"
                )

            params.update(
                {
                    "poll.fields": "duration_minutes,end_datetime,id,options,"
                    "voting_status",
                    "media.fields": "duration_ms,height,media_key,"
                    "preview_image_url,type,url,width,public_metrics",
                    "expansions": "attachments.poll_ids,"
                    "attachments.media_keys,author_id,"
                    "entities.mentions.username,geo.place_id,"
                    "in_reply_to_user_id,referenced_tweets.id,"
                    "referenced_tweets.id.author_id",
                    "tweet.fields": "attachments,author_id,"
                    "context_annotations,conversation_id,created_at,entities,"
                    "geo,id,in_reply_to_user_id,lang,public_metrics,"
                    "possibly_sensitive,referenced_tweets,source,text,"
                    "withheld",
                }
            )
            response = requests.get(
                url, headers=self.header_twitter, params=params
            )
            if not response.ok:
                response.raise_for_status()
            tweets_v2 = json.loads(response.text)
            return tweets_v2
        else:
            raise ValueError(f"API version not supported: {version}")

    def get_tweets(self):
        return self.tweets

    def get_date_last_pleroma_post(self):
        """Gathers last post from the user in Pleroma and returns the date
        of creation.

        :returns: Date of last Pleroma post in '%Y-%m-%d %H:%M:%S' format
        """
        pleroma_posts_url = (
            f"{self.pleroma_base_url}/api/v1/accounts/"
            f"{self.pleroma_username}/statuses"
        )
        response = requests.get(pleroma_posts_url, headers=self.header_pleroma)
        if not response.ok:
            response.raise_for_status()
        posts = json.loads(response.text)
        self.posts = posts
        if posts:
            date_pleroma = datetime.strftime(
                datetime.strptime(
                    posts[0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
                ),
                "%Y-%m-%d %H:%M:%S",
            )
        else:
            date_pleroma = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%d %H:%M:%S"
            )

        return date_pleroma

    def _get_pinned_tweet_id(self):
        """Retrieves the pinned tweet by the user

        :returns: ID of currently pinned tweet
        """
        url = (
            f"{self.twitter_base_url_v2}/users/"
            f"by/username/{self.twitter_username}"
        )
        params = {
            "user.fields": "pinned_tweet_id",
            "expansions": "pinned_tweet_id",
            "tweet.fields": "entities",
        }
        response = requests.get(
            url, headers=self.header_twitter, params=params
        )
        if not response.ok:
            response.raise_for_status()
        try:
            data = json.loads(response.text)
            pinned_tweet = data["includes"]["tweets"][0]
            pinned_tweet_id = pinned_tweet["id"]
        except (JSONDecodeError, KeyError):
            pinned_tweet_id = None
            pass
        return pinned_tweet_id

    def get_pinned_tweet_(self):
        return self.pinned_tweet_id

    def process_tweets(self, tweets_to_post):
        """Transforms tweets for posting them to Pleroma
        Expands shortened URLs
        Downloads tweet related media and prepares them for upload

        :param tweets_to_post: Dict of tweet objects to be processed
        :type tweets_to_post: dict
        :returns: Tweets ready to be published
        :rtype: list
        """
        for tweet in tweets_to_post["data"]:
            media = []
            # Replace shortened links
            try:
                for url_entity in tweet["entities"]["urls"]:
                    matching_pattern = url_entity["url"]
                    matches = re.findall(matching_pattern, tweet["text"])
                    for match in matches:
                        tweet["text"] = re.sub(
                            match, url_entity["expanded_url"], tweet["text"]
                        )
            except KeyError:
                # URI regex
                matching_pattern = (
                    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]"
                    r"{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*"
                    r"\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{}"
                    r';:\'".,<>?«»“”‘’]))'
                )
                matches = re.finditer(matching_pattern, tweet["text"])
                for matchNum, match in enumerate(matches, start=1):
                    # don't be brave trying to unwound an URL when it gets
                    # cut off
                    if not match.group().__contains__("…"):
                        session = requests.Session()  # so connections are
                        # recycled
                        response = session.head(
                            match.group(), allow_redirects=True
                        )
                        if not response.ok:
                            response.raise_for_status()
                        expanded_url = response.url
                        tweet["text"] = re.sub(
                            match.group(), expanded_url, tweet["text"]
                        )
            if hasattr(self, "rich_text"):
                if self.rich_text:
                    matches = re.findall(r"\B\@\w+", tweet["text"])
                    for match in matches:
                        mention_link = (
                            f"[{match}](https://"
                            f"twitter.com/"
                            f"{match[1:]})"
                        )
                        tweet["text"] = re.sub(
                            match, mention_link, tweet["text"]
                        )
            try:
                if self.nitter:
                    matching_pattern = "https://twitter.com"
                    matches = re.findall(matching_pattern, tweet["text"])
                    for match in matches:
                        tweet["text"] = re.sub(
                            match, "https://nitter.net", tweet["text"]
                        )
            except AttributeError:
                pass
            try:
                for item in tweet["attachments"]["media_keys"]:
                    for media_include in tweets_to_post["includes"]["media"]:
                        if item == media_include["media_key"]:
                            # Video download not implemented in v2 yet
                            # fallback to v1.1
                            if (
                                media_include["type"] == "video"
                                or media_include["type"] == "animated_gif"
                            ):
                                tweet_video = self._get_tweets(
                                    "v1.1", tweet["id"]
                                )
                                xmd = tweet_video["extended_entities"]["media"]
                                for extended_media in xmd:
                                    media.append(extended_media)
                            else:
                                media.append(media_include)
            except KeyError:
                pass
            # Create folder to store attachments related to the tweet ID
            tweet_path = os.path.join(self.tweets_temp_path, tweet["id"])
            if not os.path.isdir(tweet_path):
                os.mkdir(tweet_path)
            # Download media only if we plan to upload it later
            if self.media_upload:
                for idx, item in enumerate(media):
                    if (
                        item["type"] != "video"
                        and item["type"] != "animated_gif"
                    ):
                        media_url = item["url"]
                    else:
                        bitrate = 0
                        for variant in item["video_info"]["variants"]:
                            try:
                                if variant["bitrate"] >= bitrate:
                                    media_url = variant["url"]
                            except KeyError:
                                pass
                    response = requests.get(media_url, stream=True)
                    if not response.ok:
                        response.raise_for_status()
                    response.raw.decode_content = True
                    filename = str(idx) + mimetypes.guess_extension(
                        response.headers["Content-Type"]
                    )
                    with open(
                        os.path.join(
                            self.tweets_temp_path, tweet["id"], filename
                        ),
                        "wb",
                    ) as outfile:
                        shutil.copyfileobj(response.raw, outfile)

            # Process poll if exists and no media is used
            try:
                if tweet["attachments"]["poll_ids"] and not media:

                    # tweet_poll = tweet['includes']['polls']
                    poll_url = self.twitter_base_url_v2 + "/tweets"

                    params = {
                        "ids": tweet["id"],
                        "expansions": "attachments.poll_ids",
                        "poll.fields": "duration_minutes," "options",
                    }

                    response = requests.get(
                        poll_url, headers=self.header_twitter, params=params
                    )
                    if not response.ok:
                        response.raise_for_status()
                    response_content = json.loads(response.content)
                    tweet_poll = response_content["includes"]["polls"][0]

                    pleroma_poll = {
                        "options": [
                            option["label"] for option in tweet_poll["options"]
                        ],
                        "expires_in": tweet_poll["duration_minutes"] * 60,
                    }

                    # Add poll to tweet
                    tweet["polls"] = pleroma_poll

                else:
                    tweet["polls"] = None
            except KeyError:
                tweet["polls"] = None
                pass
        return tweets_to_post

    def post_pleroma(
        self, tweet_id: str, tweet_text: str, poll: dict, sensitive: bool
    ) -> str:
        """Post the given text to the Pleroma instance associated with the
        User object

        :param tweet_id: It will be used to link to the Twitter status if
        'signature' is True and to find related media
        :type tweet_id: str
        :param tweet_text: Literal text to use when creating the post.
        :type tweet_text: str
        :param poll: dict of poll if attached to tweet
        :type poll; dict
        :param sensitive: if tweet is possibly sensitive or not
        :type sensitive: bool
        :returns: id of post
        :rtype: str
        """
        # TODO: transform twitter links to nitter links, if self.nitter
        #  'true' in resolved shortened urls
        pleroma_post_url = self.pleroma_base_url + "/api/v1/statuses"
        pleroma_media_url = self.pleroma_base_url + "/api/v1/media"

        tweet_folder = os.path.join(self.tweets_temp_path, tweet_id)
        media_files = os.listdir(tweet_folder)
        media_ids = []
        if self.media_upload:
            for file in media_files:
                media_file = open(os.path.join(tweet_folder, file), "rb")
                file_size = os.stat(os.path.join(tweet_folder, file)).st_size
                mime_type = guess_type(os.path.join(tweet_folder, file))
                timestamp = str(datetime.now().timestamp())
                file_name = (
                    "pleromapyupload_"
                    + timestamp
                    + "_"
                    + random_string(10)
                    + mimetypes.guess_extension(mime_type)
                )
                file_description = (file_name, media_file, mime_type)
                files = {"file": file_description}
                response = requests.post(
                    pleroma_media_url, headers=self.header_pleroma, files=files
                )
                try:
                    if not response.ok:
                        response.raise_for_status()
                except requests.exceptions.HTTPError:
                    if response.status_code == 513:
                        logger.error("Exception occurred")
                        logger.error("Media size too large:")
                        logger.error(f"Filename: {file}")
                        logger.error(f"Size: {file_size}")
                        logger.error(
                            "Consider increasing the attachment"
                            " size limit of your instance"
                        )
                        pass
                try:
                    media_ids.append(json.loads(response.text)["id"])
                except (KeyError, JSONDecodeError):
                    print("Error uploading media:\t" + str(response.text))
                    pass

        if self.signature:
            signature = f"\n\n 🐦🔗: {self.twitter_url}/status/{tweet_id}"
            tweet_text = tweet_text + signature

        # config setting override tweet attr
        if hasattr(self, "sensitive"):
            sensitive = self.sensitive

        data = {
            "status": tweet_text,
            "sensitive": str(sensitive),
            "visibility": self.visibility,
            "media_ids[]": media_ids,
        }

        if poll:
            data.update(
                {
                    "poll[options][]": poll["options"],
                    "poll[expires_in]": poll["expires_in"],
                }
            )

        if hasattr(self, "rich_text"):
            if self.rich_text:
                data.update({"content_type": self.content_type})
        response = requests.post(
            pleroma_post_url, data, headers=self.header_pleroma
        )
        if not response.ok:
            response.raise_for_status()
        print("Post in Pleroma:\t" + str(response))
        post_id = json.loads(response.text)["id"]
        return post_id

    def pin_pleroma(self, id_post):
        """Tries to unpin previous pinned post if a file containing the ID
        of the previous post exists, then proceeds to pin the post
        with ID 'id_post'

        :param id_post: ID of post to pin
        :returns: ID of post pinned
        :rtype: str
        """
        pinned_file = os.path.join(self.user_path, "pinned_id_pleroma.txt")
        self.unpin_pleroma(pinned_file)

        pin_url = f"{self.pleroma_base_url}/api/v1/statuses/{id_post}/pin"
        response = requests.post(pin_url, headers=self.header_pleroma)
        print("Pinning post:\t" + str(response.text))
        try:
            pin_id = json.loads(response.text)["id"]
        except KeyError:
            pin_id = None
            pass
        return pin_id

    def unpin_pleroma(self, pinned_file):
        """
        Unpins post with the ID stored in the file passed as parameter
        :param pinned_file: path to file containing post ID

        """
        pinned_file_twitter = os.path.join(self.user_path, "pinned_id.txt")
        previous_pinned_post_id = None
        if os.path.isfile(pinned_file):
            with open(os.path.join(pinned_file), "r") as file:
                previous_pinned_post_id = file.readline().rstrip()
                if previous_pinned_post_id == "":
                    previous_pinned_post_id = None

        if previous_pinned_post_id:
            unpin_url = (
                f"{self.pleroma_base_url}/api/v1/statuses/"
                f"{previous_pinned_post_id}/unpin"
            )
            response = requests.post(unpin_url, headers=self.header_pleroma)
            if not response.ok:
                response.raise_for_status()
            print("Unpinning previous:\t" + response.text)
        else:
            print(
                "File with previous pinned post ID not found or empty. "
                "Checking last posts for pinned post..."
            )
            page = 0
            headers_page_url = None
            while page < 10:
                for post in self.posts:
                    if post["pinned"]:
                        with open(pinned_file, "w") as file:
                            file.write(post["id"] + "\n")
                        return self.unpin_pleroma(pinned_file)
                page += 1
                pleroma_posts_url = (
                    f"{self.pleroma_base_url}/api/v1/accounts/"
                    f"{self.pleroma_username}/statuses"
                )
                if headers_page_url:
                    statuses_url = headers_page_url
                else:
                    statuses_url = pleroma_posts_url
                response = requests.get(
                    statuses_url, headers=self.header_pleroma
                )
                if not response.ok:
                    response.raise_for_status()
                posts = json.loads(response.text)
                self.posts = posts
                links = requests.utils.parse_header_links(
                    response.headers["link"].rstrip(">").replace(">,<", ",<")
                )
                for link in links:
                    if link["rel"] == "next":
                        headers_page_url = link["url"]

            logger.warning("Pinned post not found. Giving up unpinning...")
        # Clear pinned ids
        with open(pinned_file, "w") as file:
            file.write("\n")
        with open(pinned_file_twitter, "w") as file:
            file.write("\n")

    def update_pleroma(self):
        """Update the Pleroma user info with the one retrieved from Twitter
        when the User object was instantiated.
        This includes:

        * Profile image (if exists)
        * Banner image (if exists)
        * Bio text
        * Screen name
        * Additional metadata fields

        :returns: None
        """
        # Get the biggest resolution for the profile picture (400x400)
        # instead of 'normal'
        if self.profile_image_url:
            profile_img_big = re.sub(
                r"normal", "400x400", self.profile_image_url
            )
            response = requests.get(profile_img_big, stream=True)
            if not response.ok:
                response.raise_for_status()
            response.raw.decode_content = True
            with open(self.avatar_path, "wb") as outfile:
                shutil.copyfileobj(response.raw, outfile)

        if self.profile_banner_url:
            response = requests.get(self.profile_banner_url, stream=True)
            if not response.ok:
                response.raise_for_status()
            response.raw.decode_content = True
            with open(self.header_path, "wb") as outfile:
                shutil.copyfileobj(response.raw, outfile)

        # Set it on Pleroma
        cred_url = (
            f"{self.pleroma_base_url}/api/v1/" f"accounts/update_credentials"
        )

        # Construct fields
        fields = []
        for field_item in self.fields:
            field = (field_item["name"], field_item["value"])
            fields.append(field)
        data = {"note": self.bio_text, "display_name": self.display_name}

        if self.profile_image_url:
            data.update({"avatar": self.avatar_path})

        if self.profile_banner_url:
            data.update({"header": self.header_path})

        if len(fields) > 4:
            raise Exception(
                f"Total number of metadata fields cannot exceed 4."
                f"Provided: {len(fields)}. Exiting..."
            )
        for idx, (field_name, field_value) in enumerate(fields):
            data["fields_attributes[" + str(idx) + "][name]"] = field_name
            data["fields_attributes[" + str(idx) + "][value]"] = field_value

        if self.profile_image_url:
            avatar = open(self.avatar_path, "rb")
            avatar_mime_type = guess_type(self.avatar_path)
            timestamp = str(datetime.now().timestamp())
            avatar_file_name = (
                f"pleromapyupload_{timestamp}_"
                f"{random_string(10)}"
                f"{mimetypes.guess_extension(avatar_mime_type)}"
            )
        if self.profile_banner_url:
            header = open(self.header_path, "rb")
            header_mime_type = guess_type(self.header_path)
            header_file_name = (
                f"pleromapyupload_{timestamp}_"
                f"{random_string(10)}"
                f"{mimetypes.guess_extension(header_mime_type)}"
            )

        files = {}

        if self.profile_image_url:
            files.update(
                {"avatar": (avatar_file_name, avatar, avatar_mime_type)}
            )
        if self.profile_banner_url:
            files.update(
                {"header": (header_file_name, header, header_mime_type)}
            )
        response = requests.patch(
            cred_url, data, headers=self.header_pleroma, files=files
        )
        if not response.ok:
            response.raise_for_status()
        print("Updating profile:\t" + str(response))  # for debugging
        return

    def check_pinned(self):
        """
        Checks if a tweet is pinned and needs to be retrieved and posted on the
        Fediverse account
        """
        print("Current pinned:\t" + str(self.pinned_tweet_id))
        pinned_file = os.path.join(self.user_path, "pinned_id.txt")
        if os.path.isfile(pinned_file):
            with open(pinned_file, "r") as file:
                previous_pinned_tweet_id = file.readline().rstrip()
                if previous_pinned_tweet_id == "":
                    previous_pinned_tweet_id = None
        else:
            previous_pinned_tweet_id = None
        print("Previous pinned:\t" + str(previous_pinned_tweet_id))
        if (
            self.pinned_tweet_id != previous_pinned_tweet_id
            and self.pinned_tweet_id is not None
        ):
            pinned_tweet = self._get_tweets("v2", self.pinned_tweet_id)
            tweets_to_post = {
                "data": [pinned_tweet["data"]],
                "includes": pinned_tweet["includes"],
            }
            tweets_to_post = self.process_tweets(tweets_to_post)
            id_post_to_pin = self.post_pleroma(
                self.pinned_tweet_id,
                tweets_to_post["data"][0]["text"],
                tweets_to_post["data"][0]["polls"],
                tweets_to_post["data"][0]["possibly_sensitive"],
            )
            pleroma_pinned_post = self.pin_pleroma(id_post_to_pin)
            with open(pinned_file, "w") as file:
                file.write(self.pinned_tweet_id + "\n")
            if pleroma_pinned_post is not None:
                with open(
                    os.path.join(self.user_path, "pinned_id_pleroma.txt"), "w"
                ) as file:
                    file.write(pleroma_pinned_post + "\n")
        elif (
            self.pinned_tweet_id != previous_pinned_tweet_id
            and previous_pinned_tweet_id is not None
        ):
            pinned_file = os.path.join(self.user_path, "pinned_id_pleroma.txt")
            self.unpin_pleroma(pinned_file)

    def replace_vars_in_str(self, text: str, var_name: str = None) -> str:
        """
        Returns a string with "{{ var_name }}" replaced with var_name's value
        If no 'var_name' is provided, locals() (or self if it's an object
        method) will be used and all variables found in locals() (or object
        attributes) will be replaced with their values.

        :param text: String to be parsed, replacing "{{ var_name }}" with
        var_name's value. Multiple occurrences are supported.
        :type text: str
        :param var_name: Name of the variable to be replace. Multiple
        occurrences are supported. If not provided, locals() will be used and
        all variables will be replaced with their values.
        :type var_name: str

        :returns: A string with {{ var_name }} replaced with var_name's value.
        :rtype: str
        """
        # Jinja-style string replacement i.e. vars encapsulated in {{ and }}
        if var_name is not None:
            matching_pattern = r"(?<=\{{)( " + var_name + r" )(?=\}})"
            matches = re.findall(matching_pattern, text)
        else:
            matches = re.findall(r"(?<={{)(.*?)(?=}})", text)
        for match in matches:
            pattern = r"{{ " + match.strip() + " }}"
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
    :returns: an alpha-numerical string of specified length with random
    characters
    :rtype: str
    """
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def main():
    try:
        base_path = os.getcwd()
        with open(os.path.join(base_path, "config.yml"), "r") as stream:
            config = yaml.safe_load(stream)
        user_dict = config["users"]

        for user_item in user_dict:
            user = User(user_item, config)
            date_pleroma = user.get_date_last_pleroma_post()
            tweets = user.get_tweets()
            # Put oldest first to iterate them and post them in order
            tweets["data"].reverse()
            tweets_to_post = {"data": [], "includes": tweets["includes"]}
            # Get rid of old tweets
            for tweet in tweets["data"]:
                created_at = tweet["created_at"]
                date_twitter = datetime.strftime(
                    datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.000Z"),
                    "%Y-%m-%d %H:%M:%S",
                )
                if date_twitter > date_pleroma:
                    tweets_to_post["data"].append(tweet)

            tweets_to_post = user.process_tweets(tweets_to_post)
            print("tweets:", tweets_to_post["data"])
            for tweet in tweets_to_post["data"]:
                user.post_pleroma(
                    tweet["id"],
                    tweet["text"],
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


if __name__ == "__main__":
    exit(main())
