import os
import re
import json
import html
import shutil
import requests
import mimetypes
from datetime import datetime

from tqdm import tqdm

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from . import logger
from .i18n import _
from pleroma_bot._twitter import twitter_api_request


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
    # Remove quote tweets if include_quotes is false
    if not self.include_quotes:  # pragma: todo
        for tweet in tweets_to_post["data"][:]:
            try:
                for reference in tweet["referenced_tweets"]:
                    if reference["type"] == "quoted":
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
    all_media = []
    if int(self.threads) == 1:
        desc = _("Processing tweets... ")
        pbar = tqdm(total=len(tweets_to_post["data"]), desc=desc)

    for idx, tweet in enumerate(tweets_to_post["data"]):
        # logger.info(_("Processing: {}/{}").format(idx+1, total_tweets))
        self.posts_ids[self.pleroma_base_url].update({tweet["id"]: ''})
        tweet["reply_id"] = None
        tweet["retweet_id"] = None
        # get reply ids
        if "referenced_tweets" in tweet.keys():
            for reference in tweet["referenced_tweets"]:
                if reference["type"] == "replied_to":
                    tweet["reply_id"] = reference["id"]
                if reference["type"] == "retweeted":
                    tweet["retweet_id"] = reference["id"]
        media = []
        logger.debug(tweet["id"])
        # Get full text from RT or quoted tweet
        if "referenced_tweets" in tweet.keys():  # pragma: no cover
            tweet["text"] = _get_rt_text(self, tweet)
        tweet["text"] = _expand_urls(self, tweet)
        tweet["text"] = html.unescape(tweet["text"])

        # Download media only if we plan to upload it later
        if self.media_upload and not self.archive:
            if self.guest:  # pragma: todo
                if "extended_entities" in tweet:
                    if "media" in tweet['extended_entities']:
                        for item in tweet['extended_entities']['media']:
                            media.append(item)
            try:
                media_keys = False
                attachments = "attachments" in tweet.keys()
                if attachments:
                    tweet_attachments = tweet["attachments"]
                    media_keys = "media_keys" in tweet_attachments.keys()
                if media_keys and attachments:
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
                    _get_rt_media_url(self, tweet, media)
            except KeyError:
                pass
            if len(media) > 0:
                # Create folder to store attachments related to the tweet ID
                tweet_path = os.path.join(self.tweets_temp_path, tweet["id"])
                os.makedirs(tweet_path, exist_ok=True)
                _download_media(self, media, tweet)
                all_media.extend(media)

        if not self.keep_media_links:
            tweet["text"] = _remove_media_links(self, tweet)
            tweet["text"] = _remove_status_links(self, tweet)
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
        signature = ''
        if self.signature:
            if self.archive:  # pragma: todo
                t_user = self.twitter_ids[list(self.twitter_ids.keys())[0]]
            else:
                t_user = "i/web"
                if tweet["author_id"] in self.twitter_ids:
                    t_user = self.twitter_ids[tweet["author_id"]]
            twitter_url_user = f"{self.twitter_url_home}/{t_user}"
            signature = f"\n\n 🐦🔗: {twitter_url_user}/status/{tweet['id']}"
            if self.instance == "mastodon":  # pragma: todo
                len_text = self._mastodon_len(tweet["text"])
                len_signature = self._mastodon_len(signature)
            else:
                len_text = len(tweet["text"])
                len_signature = len(signature)
            total_length = len_text + len_signature
            if total_length > self.max_post_length:  # pragma
                body_max_length = self.max_post_length - len_signature - 1
                tweet["text"] = f"{tweet['text'][:body_max_length]}…"
            tweet["text"] = f"{tweet['text']}{signature}"
        if self.original_date:
            tweet_date = tweet["created_at"]
            date = datetime.strftime(
                datetime.strptime(tweet_date, "%Y-%m-%dT%H:%M:%S.000Z"),
                self.original_date_format,
            )
            orig_date = f"\n\n[{date}]"
            if self.instance == "mastodon":  # pragma: todo
                len_text = self._mastodon_len(tweet["text"])
            else:
                len_text = len(tweet["text"])
            total_length = len_text + len(orig_date)
            if total_length > self.max_post_length:  # pragma
                if self.signature:
                    tweet["text"] = tweet["text"].replace(signature, '')
                l_date = len(orig_date)
                if self.instance == "mastodon":
                    l_sig = self._mastodon_len(signature)
                else:
                    l_sig = len(signature)
                body_max_length = self.max_post_length - l_date - l_sig - 1
                tweet["text"] = f"{tweet['text'][:body_max_length]}…"
            else:
                signature = ''
            tweet["text"] = f"{tweet['text']}{signature}{orig_date}"
        # Process poll if exists and no media is used
        tweet["polls"] = _process_polls(self, tweet, media)

        # Truncate text if needed
        if self.instance == "mastodon":  # pragma: todo
            total_tweet_length = self._mastodon_len(tweet["text"])
        else:
            total_tweet_length = len(tweet["text"])
        if total_tweet_length > self.max_post_length:  # pragma
            logger.info(
                _(
                    "Post text longer than allowed ({}), truncating..."
                ).format(self.max_post_length)
            )
            tweet["text"] = f"{tweet['text'][:self.max_post_length]}"
        if int(self.threads) == 1:
            pbar.update(1)
    tweets_to_post["media_processed"] = all_media
    return tweets_to_post


def _get_rt_text(self, tweet):  # pragma: no cover
    text = tweet["text"]

    for reference in tweet["referenced_tweets"]:
        retweeted = reference["type"] == "retweeted"
        quoted = reference["type"] == "quoted"
        if retweeted or quoted:
            tweet_ref_id = reference["id"]
            tweet_ref = self._get_tweets("v2", tweet_ref_id)

            match = re.search(r"RT.*?\:", tweet["text"])
            prefix = match.group() if match else ""
            if retweeted:
                text = f"{prefix} {tweet_ref['data']['text']}"
            elif quoted:
                author = tweet_ref["data"]["author_id"]
                users = tweet_ref["includes"]["users"]
                username = [u["username"] for u in users if author == u["id"]]
                prefix = f"RT @{username[0]}:"
                text = f"{tweet['text']}\n{prefix} {tweet_ref['data']['text']}"
        else:
            break
    return text


def _get_rt_media_url(self, tweet, media):  # pragma: no cover
    tweet_rt = {"data": tweet}
    tw_data = tweet_rt["data"]
    i = 0
    max_at = self.max_attachments
    while "referenced_tweets" in tw_data.keys() and len(media) < max_at:
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
                                tw_data
                            )
                            if media_url:
                                new = [
                                    i for i in media_url if i["url"] not in [
                                        j["url"] for j in media
                                    ]
                                ]
                                media.extend(new)
                if self.guest:  # pragma: todo
                    if "extended_entities" in tw_data:
                        if "media" in tw_data['extended_entities']:
                            for item in tw_data['extended_entities']['media']:
                                if item not in media:
                                    media.append(item)
            else:
                break
        i += 1
        if i > 3:
            logger.debug(
                _("Giving up, reference is too deep")
            )
            break


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

            response = twitter_api_request(
                'GET',
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
            if "media_url" in item:  # pragma: todo
                media_url = item['media_url']
            else:
                media_url = item["url"]
        else:
            media_url = _get_best_bitrate_video(self, item)

        if media_url:
            key = item["media_key"] if not (
                self.archive or self.rss
            ) else item["id"]
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
                    ).format(tweet=tweet["id"], media_url=media_url)
                    logger.warning(att_not_found)
                    continue
                elif response.status_code == 403:
                    geoblocked = _(
                        "Media possibly geoblocked? (403) Skipping... "
                        "{tweet} - {media_url} "
                    ).format(tweet=tweet["id"], media_url=media_url)
                    logger.warning(geoblocked)
                    continue
                else:
                    response.raise_for_status()
            response.raw.decode_content = True
            filename = str(idx) + "-" + key + mimetypes.guess_extension(
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


def _remove_status_links(self, tweet):
    regex = r"\bhttps?:\/\/twitter.com\/+[^\/:]+\/.*?status\/\d*\b"
    tweet["text"] = re.sub(regex, '', tweet["text"], 0, re.MULTILINE)
    return tweet["text"]


def _remove_media_links(self, tweet):
    regex = r"\bhttps?:\/\/twitter.com\/+[^\/:]+\/.*?(photo|video)\/\d*\b"
    tweet["text"] = re.sub(regex, '', tweet["text"], 0, re.MULTILINE)
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

    # URI regex
    matching_pattern = (
        r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]"
        r"{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*"
        r"\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{}"
        r';:\'".,<>?«»“”‘’]))'
    )
    matches = re.finditer(matching_pattern, tweet["text"])
    urls = {}
    # Prepare a session to recycle connections across requests
    session = requests.Session()
    # Replace shortened links
    for matchNum, match in enumerate(matches, start=1):
        group = match.group()
        try:
            if len(tweet["entities"]["urls"]) > 0:
                entities_urls = tweet["entities"]["urls"]
                urls = {
                    u["url"]: u["expanded_url"] for u in entities_urls
                }
            if group in urls.keys():
                tweet["text"] = re.sub(group, urls[group], tweet["text"])
            else:
                raise KeyError
        except (KeyError, TypeError):
            # don't be brave trying to unwound an URL when it gets cut off
            if (
                    not group.__contains__("…") and not
                    group.startswith(self.nitter_base_url)
            ):
                if not group.startswith(("http://", "https://")):
                    group = f"http://{group}"
                try:
                    response = session.head(
                        group,
                        allow_redirects=True,
                        timeout=(7, 10)
                    )
                    if not response.ok:
                        logger.debug(
                            _(
                                "Couldn't expand the url {}: {}"
                            ).format(group, response.status_code)
                        )
                    if response:
                        expanded_url = response.url
                        tweet["text"] = re.sub(
                            group, expanded_url, tweet["text"]
                        )
                except Exception as ex:  # pragma
                    logger.debug(
                        _(
                            "Couldn't expand the url: {}"
                        ).format(group)
                    )
                    if isinstance(ex, requests.exceptions.RequestException):
                        expanded_url = ex.request.url
                        tweet["text"] = re.sub(
                            group, expanded_url, tweet["text"]
                        )
                        pass
                    elif isinstance(ex, UnicodeError):
                        expanded_url = ex.object.decode('latin1')
                        tweet["text"] = re.sub(
                            group, expanded_url, tweet["text"]
                        )
                        pass
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
                extended_media["media_key"] = item
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
