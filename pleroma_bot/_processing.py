import os
import re
import json
import html
import shutil
import requests
import mimetypes
from datetime import datetime


# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from . import logger
from .i18n import _


def process_tweets(self, tweets_to_post):
    """Transforms tweets for posting them to Pleroma
    Expands shortened URLs
    Downloads tweet related media and prepares them for upload

    :param tweets_to_post: Dict of tweet objects to be processed
    :type tweets_to_post: dict
    :returns: Tweets ready to be published
    :rtype: list
    """
    # TODO: Break into smaller functions

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

    if self.hashtags:
        for tweet in tweets_to_post["data"][:]:
            try:
                tweet_hashtags = tweet["entities"]["hashtags"]
                i = 0
                while i < len(tweet_hashtags):
                    if tweet_hashtags[i]["tag"] in self.hashtags:
                        break
                    i += 1
                else:
                    tweets_to_post["data"].remove(tweet)
            except KeyError:
                tweets_to_post["data"].remove(tweet)
                pass

    for tweet in tweets_to_post["data"]:
        media = []
        logger.debug(tweet["id"])
        tweet["text"] = _expand_urls(self, tweet)
        tweet["text"] = html.unescape(tweet["text"])

        # Download media only if we plan to upload it later
        if self.media_upload:
            try:
                if self.archive:
                    for item in tweet["extended_entities"]["media"]:
                        if item["type"] == "photo":
                            item["url"] = item["media_url"]
                        media.append(item)
                else:
                    m_k = False
                    att = "attachments" in tweet.keys()
                    if att:
                        m_k = "media_keys" in tweet["attachments"].keys()
                    if m_k and att:
                        includes_media = tweets_to_post["includes"]["media"]
                        for item in tweet["attachments"]["media_keys"]:
                            for media_include in includes_media:
                                media_url = _get_media_url(
                                    self, item, media_include, tweet
                                )
                                if media_url:
                                    media.extend(media_url)
                    # Get RT tweet media
                    if "referenced_tweets" in tweet.keys():  # pragma: no cover
                        tweet_rt = {"data": tweet}
                        tw_data = tweet_rt["data"]
                        i = 0
                        while "referenced_tweets" in tw_data.keys():
                            for reference in tw_data["referenced_tweets"]:
                                retweeted = reference["type"] == "retweeted"
                                quoted = reference["type"] == "quoted"
                                if retweeted or quoted:
                                    tweet_id = reference["id"]
                                    tweet_rt = self._get_tweets("v2", tweet_id)
                                    tw_data = tweet_rt["data"]
                                    att = "attachments" in tw_data.keys()
                                    if att:
                                        attachments = tw_data["attachments"]
                                        in_md = tweet_rt["includes"]["media"]
                                        md_keys = attachments["media_keys"]
                                        for item in md_keys:
                                            for media_include in in_md:
                                                media_url = _get_media_url(
                                                    self,
                                                    item,
                                                    media_include,
                                                    tweet_rt
                                                )
                                                if media_url:
                                                    media.extend(media_url)
                                else:
                                    break
                            i += 1
                            if i > 3:
                                logger.debug(
                                    _("Giving up, reference is too deep")
                                )
                                break
            except KeyError:
                pass
            if len(media) > 0:
                # Create folder to store attachments related to the tweet ID
                tweet_path = os.path.join(self.tweets_temp_path, tweet["id"])
                os.makedirs(tweet_path, exist_ok=True)
                _download_media(self, media, tweet)

        if not self.keep_media_links:
            tweet["text"] = _remove_media_links(self, tweet)
        if hasattr(self, "rich_text"):
            if self.rich_text:
                tweet["text"] = _replace_mentions(self, tweet)
        if self.nitter:
            tweet["text"] = _replace_url(
                self,
                tweet["text"],
                "https://twitter.com",
                self.nitter_base_url
            )
        if self.invidious:
            tweet["text"] = _replace_url(
                self,
                tweet["text"],
                "https://youtube.com",
                self.invidious_base_url
            )
        if self.signature:
            if self.archive:
                t_user = self.twitter_ids[list(self.twitter_ids.keys())[0]]
            else:
                t_user = self.twitter_ids[tweet["author_id"]]
            twitter_url = self.twitter_url[t_user]
            signature = f"\n\n 🐦🔗: {twitter_url}/status/{tweet['id']}"
            tweet["text"] = f"{tweet['text']} {signature}"
        if self.original_date:
            tweet_date = tweet["created_at"]
            date = datetime.strftime(
                datetime.strptime(tweet_date, "%Y-%m-%dT%H:%M:%S.000Z"),
                self.original_date_format,
            )
            tweet["text"] = f"{tweet['text']} \n\n[{date}]"
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
                poll_url,
                headers=self.header_twitter,
                params=params,
                auth=self.auth
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
                    att_not_found = _(
                        "Exception occurred"
                        "\nMedia not found (404)"
                        "\n{tweet} - {media_url}"
                        "\nIgnoring attachment and continuing..."
                    ).format(tweet=tweet, media_url=media_url)
                    logger.warning(att_not_found)
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
                        _(
                            "Attachment exceeded config file size limit ({})"
                        ).format(self.file_max_size)
                    )
                    logger.error(
                        _("File size: {}MB").format(
                            round(file_size_bytes / 2 ** 20, 2)
                        )
                    )
                    logger.error(_("Ignoring attachment and continuing..."))
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


def _replace_url(self, data, url, new_url):
    matches = re.findall(url, data)
    for match in matches:
        data = re.sub(match, new_url, data)
    return data


def _remove_media_links(self, tweet):
    regex = r"\bhttps?:\/\/twitter.com\/+[^\/:]+\/.*?(photo|video)\/\d*\b"
    match = re.search(regex, tweet["text"])
    if match:
        tweet["text"] = re.sub(match.group(), '', tweet["text"])
    return tweet["text"]


def _replace_mentions(self, tweet):
    matches = re.findall(r"\B\@\w+", tweet["text"])
    for match in matches:
        # TODO: Use nitter if asked (self.nitter)
        mention_link = f"[{match}](https://twitter.com/{match[1:]})"
        tweet["text"] = re.sub(match, mention_link, tweet["text"])
    return tweet["text"]


def _expand_urls(self, tweet):
    # TODO: transform twitter links to nitter links, if self.nitter
    #  'true' in resolved shortened urls

    # Replace shortened links
    try:
        if len(tweet["entities"]["urls"]) == 0:
            raise KeyError
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
            group = match.group()
            # don't be brave trying to unwound an URL when it gets
            # cut off
            if (
                    not group.__contains__("…") and not
                    group.startswith(self.nitter_base_url)
            ):
                if not group.startswith(("http://", "https://")):
                    group = f"http://{group}"
                # so connections are recycled
                session = requests.Session()
                response = session.head(group, allow_redirects=True)
                if not response.ok:
                    logger.debug(
                        _(
                            "Couldn't expand the {}: {}"
                        ).format(response.url, response.status_code)
                    )
                    response.raise_for_status()
                else:
                    expanded_url = response.url
                    tweet["text"] = re.sub(
                        group, expanded_url, tweet["text"]
                    )
    return tweet["text"]


def _get_media_url(self, item, media_include, tweet):
    # TODO: Verify if video download is available on v2 and migrate to it
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
    url = ""
    for variant in item["video_info"]["variants"]:
        try:
            if "bitrate" in variant:
                if int(variant["bitrate"]) >= bitrate:
                    bitrate = int(variant["bitrate"])
                    url = variant["url"]
            else:
                continue
        except KeyError:  # pragma: no cover
            pass
    return url
