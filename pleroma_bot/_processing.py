import os
import re
import json
import html
import shutil
import requests
import mimetypes

from ._utils import spinner

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from . import logger


@spinner("Processing tweets... ")
def process_tweets(self, tweets_to_post):
    """Transforms tweets for posting them to Pleroma
    Expands shortened URLs
    Downloads tweet related media and prepares them for upload

    :param tweets_to_post: Dict of tweet objects to be processed
    :type tweets_to_post: dict
    :returns: Tweets ready to be published
    :rtype: list
    """
    # Remove RTs if include_rts is false
    if not self.include_rts:
        for tweet in tweets_to_post["data"][:]:
            try:
                for reference in tweet["referenced_tweets"]:
                    if reference["type"] == "retweeted":
                        tweets_to_post["data"].remove(tweet)
                        break
            except KeyError:
                pass
    # Remove replies if include_replies is false
    if not self.include_replies:
        for tweet in tweets_to_post["data"][:]:
            try:
                for reference in tweet["referenced_tweets"]:
                    if reference["type"] == "replied_to":
                        tweets_to_post["data"].remove(tweet)
                        break
            except KeyError:
                pass
    for tweet in tweets_to_post["data"]:
        media = []
        tweet["text"] = _expand_urls(self, tweet)
        tweet["text"] = html.unescape(tweet["text"])
        if hasattr(self, "rich_text"):
            if self.rich_text:
                tweet["text"] = _replace_mentions(self, tweet)
        try:
            if self.nitter:
                tweet["text"] = _replace_nitter(self, tweet)
        except AttributeError:
            pass
        try:
            for item in tweet["attachments"]["media_keys"]:
                for media_include in tweets_to_post["includes"]["media"]:
                    media_url = _get_media_url(
                        self, item, media_include, tweet
                    )
                    if media_url:
                        media.extend(media_url)
        except KeyError:
            pass
        # Create folder to store attachments related to the tweet ID
        tweet_path = os.path.join(self.tweets_temp_path, tweet["id"])
        os.makedirs(tweet_path, exist_ok=True)
        # Download media only if we plan to upload it later
        if self.media_upload:
            _download_media(self, media, tweet)
        # Process poll if exists and no media is used
        tweet["polls"] = _process_polls(self, tweet, media)

    return tweets_to_post


def _process_polls(self, tweet, media):
    try:
        if tweet["attachments"]["poll_ids"] and not media:

            # tweet_poll = tweet['includes']['polls']
            poll_url = f"{self.twitter_base_url_v2}/tweets"

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

    return tweet["polls"]


def _download_media(self, media, tweet):
    for idx, item in enumerate(media):
        if item["type"] != "video" and item["type"] != "animated_gif":
            media_url = item["url"]
        else:
            media_url = _get_best_bitrate_video(self, item)

        if media_url:
            response = requests.get(media_url, stream=True)
            try:
                if not response.ok:
                    response.raise_for_status()
            except requests.exceptions.HTTPError:
                if response.status_code == 404:
                    logger.warning("Exception occurred")
                    logger.warning("Media not found (404)")
                    logger.warning(f"{tweet} - {media_url}")
                    logger.warning("Ignoring attachment and continuing...")
                    return
                else:
                    response.raise_for_status()
            response.raw.decode_content = True
            filename = str(idx) + mimetypes.guess_extension(
                response.headers["Content-Type"]
            )
            file_path = os.path.join(
                self.tweets_temp_path, tweet["id"], filename
            )
            with open(file_path, "wb") as outfile:
                shutil.copyfileobj(response.raw, outfile)
            # Remove attachment if exceeds the limit
            if hasattr(self, "file_max_size"):
                file_size_bytes = os.stat(file_path).st_size
                max_file_size_bytes = parse_size(self.file_max_size)
                if file_size_bytes > max_file_size_bytes:
                    logger.error(
                        f"Attachment exceeded config file size limit "
                        f"({self.file_max_size})"
                    )
                    logger.error(
                        f"File size: {round(file_size_bytes / 2 ** 20, 2)}MB"
                    )
                    logger.error("Ignoring attachment and continuing...")
                    os.remove(file_path)


def parse_size(size):
    units = {
        "B": 1,
        "KB": 2 ** 10,
        "MB": 2 ** 20,
        "GB": 2 ** 30,
        "TB": 2 ** 40,
    }
    size = size.upper()
    if not re.match(r" ", size):
        size = re.sub(r"([KMGT]?B)", r" \1", size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * units[unit])


def _replace_nitter(self, tweet):
    matching_pattern = "https://twitter.com"
    matches = re.findall(matching_pattern, tweet["text"])
    for match in matches:
        tweet["text"] = re.sub(match, self.nitter_base_url, tweet["text"])
    return tweet["text"]


def _replace_mentions(self, tweet):
    matches = re.findall(r"\B\@\w+", tweet["text"])
    for match in matches:
        mention_link = f"[{match}](https://twitter.com/{match[1:]})"
        tweet["text"] = re.sub(match, mention_link, tweet["text"])
    return tweet["text"]


def _expand_urls(self, tweet):
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
                response = session.head(match.group(), allow_redirects=True)
                if not response.ok:
                    response.raise_for_status()
                expanded_url = response.url
                tweet["text"] = re.sub(
                    match.group(), expanded_url, tweet["text"]
                )
    return tweet["text"]


def _get_media_url(self, item, media_include, tweet):
    media_urls = []
    if item == media_include["media_key"]:
        # Video download not implemented in v2 yet
        # fallback to v1.1
        if (
            media_include["type"] == "video"
            or media_include["type"] == "animated_gif"
        ):
            tweet_video = self._get_tweets("v1.1", tweet["id"])
            xmd = tweet_video["extended_entities"]["media"]
            for extended_media in xmd:
                media_urls.append(extended_media)
            return media_urls
        else:
            media_urls.append(media_include)
            return media_urls


def _get_best_bitrate_video(self, item):
    bitrate = 0
    for variant in item["video_info"]["variants"]:
        try:
            if variant["bitrate"] >= bitrate:
                return variant["url"]
        except KeyError:
            pass
