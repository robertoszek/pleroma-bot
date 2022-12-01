import os
import re
import sys
import time
import json
import string
import random
import shutil
import zipfile
import tempfile
import requests
import warnings
import threading
import functools
import mimetypes

from tqdm import tqdm
from typing import cast
from errno import ENOENT
from multiprocessing import Queue, Pool
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
from itertools import tee, islice, chain, cycle
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

if sys.platform == "win32":  # pragma: win32 cover
    import msvcrt  # pragma: win32 cover
else:
    try:
        import fcntl
    except ImportError:  # pragma: win32 cover
        pass  # pragma: win32 cover

from .i18n import _
from . import logger
from ._error import TimeoutLocker


def spinner(
        message, wait: float = 0.3, spinner_symbols: list = None
):  # pragma: deprecated
    """
    Decorator that launches the function wrapped and the spinner each in a
    separate thread
    :param wait: time to wait between symbol cycles
    :param message: Message to display next to the spinner
    :param spinner_symbols:
    :return:
    """
    spinner_symbols = spinner_symbols or list("|/-\\")
    spinner_symbols = cycle(spinner_symbols)
    global input_thread

    def start():
        while input_thread.is_alive():
            symbol = next(spinner_symbols)
            print(
                "\r{message} {symbol}".format(message=message, symbol=symbol),
                end="",
            )
            time.sleep(wait)

    def stop():
        print("\r", end="")

    def external(fct):
        @functools.wraps(fct)
        def wrapper(*args, **kwargs):
            return_que = Queue()
            global input_thread
            input_thread = PropagatingThread(
                target=lambda q, *arg1, **kwarg1: q.put(fct(*arg1, **kwarg1)),
                args=(return_que, *args),
                kwargs=dict(**kwargs),
            )
            input_thread.start()
            spinner_thread = threading.Thread(target=start)
            spinner_thread.start()

            spinner_thread.join()
            input_thread.join()
            stop()

            result = return_que.get()

            return result

        return wrapper

    return external


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def process_parallel(tweets, user, threads):
    dt = tweets["data"]
    chunks = chunkify(dt, threads)
    # mp = Multiprocessor()
    tweets_chunked = []
    for idx in range(threads):
        tweets_chunked.append({
            "data": chunks[idx],
            "includes": tweets["includes"],
            "meta": tweets["meta"]
        })
    with Pool(threads) as p:
        ret = []
        desc = _("Processing tweets... ")
        with tqdm(total=len(dt), desc=desc) as pbar:
            for idx, res in enumerate(
                    p.imap_unordered(user.process_tweets, tweets_chunked)
            ):
                pbar.update(len(chunks[idx]))
                ret.append(res)

    tweets_merged = {
        "data": [],
        "includes": tweets["includes"],
        "meta": tweets["meta"],
        "media_processed": []
    }
    for idx in range(threads):
        tweets_merged["data"].extend(ret[idx]["data"])
        tweets_merged["media_processed"].extend(ret[idx]["media_processed"])
    tweets_merged["data"] = sorted(
        tweets_merged["data"], key=lambda i: i["created_at"]
    )
    return tweets_merged


class Multiprocessor:  # pragma: deprecated

    def __init__(self):
        self.processes = []
        self.queue = Queue()

    @staticmethod
    def _wrapper(func, queue, args, kwargs):
        ret = func(*args, **kwargs)
        queue.put(ret)

    def run(self, func, *args, **kwargs):
        args2 = [func, self.queue, args, kwargs]
        p = PropagatingThread(target=self._wrapper, args=args2)
        self.processes.append(p)
        p.start()

    # @spinner(_("Processing tweets... "), 1.2)
    def wait(self):
        rets = []
        for p in self.processes:
            ret = self.queue.get()
            rets.append(ret)
        for p in self.processes:
            p.join()
        return rets


class PropagatingThread(threading.Thread):  # pragma: deprecated
    """
    Thread that surfaces exceptions that occur inside of it
    """

    def run(self):
        self.exc = None
        # Event to keep track if thread has started
        self.started_evt = threading.Event()
        try:
            self.ret = self._target(*self._args, **self._kwargs)
            self.started_evt.set()
        except BaseException as e:
            self.exc = e
            self.started_evt.clear()

    def join(self):
        if not self.exc:
            self.started_evt.wait()
        super(PropagatingThread, self).join()
        self.started_evt.clear()
        if self.exc:
            raise self.exc
        return self.ret


class Locker:
    """
    Context manager that creates lock file
    """

    def __init__(self, lock_filename=None, timeout=5):
        self.timeout = timeout
        if lock_filename:
            self._lock_file = lock_filename
        else:
            module_name = __loader__.name.split('.')[0]
            lock_filename = f"{module_name}.lock"
            self.tmp = tempfile.gettempdir()
            self._lock_file = os.path.join(self.tmp, lock_filename)
        self.mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        self._lock_file_fd = None

    @property
    def is_locked(self):
        return self._lock_file_fd is not None

    def acquire(self):
        lock_id = id(self)
        lock_filename = self._lock_file
        start_time = time.time()
        poll_interval = 1.0
        while True:
            if not self.is_locked:
                logger.debug(
                    _(
                        "Attempting to acquire lock {} on {}"
                    ).format(lock_id, lock_filename)
                )
                self._acquire()

            if self.is_locked:
                logger.debug(
                    _("Lock {} acquired on {}").format(lock_id, lock_filename)
                )
                break
            elif 0 <= self.timeout < time.time() - start_time:
                logger.debug(
                    _(
                        "Timeout on acquiring lock {} on {}"
                    ).format(lock_id, lock_filename)
                )
                raise TimeoutLocker(self._lock_file)
            else:
                msg = _(
                    "Lock {} not acquired on {}, waiting {} seconds ..."
                )
                logger.info(
                    msg.format(lock_id, lock_filename, poll_interval)
                )
                time.sleep(poll_interval)

    def _acquire(self):
        if sys.platform == "win32":  # pragma: win32 cover
            try:
                fd = os.open(self._lock_file, self.mode)
            except OSError as exception:
                if exception.errno == ENOENT:  # No such file or directory
                    raise
            else:
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                except OSError:
                    os.close(fd)
                else:
                    self._lock_file_fd = fd
        else:
            fd = os.open(self._lock_file, self.mode)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
            else:
                self._lock_file_fd = fd

    def release(self):
        if self.is_locked:  # pragma: no cover
            lock_id, lock_filename = id(self), self._lock_file
            logger.debug(
                _(
                    "Attempting to release lock {} on {}"
                ).format(lock_id, lock_filename)
            )
            self._release()
            logger.debug(
                _("Lock {} released on {}").format(lock_id, lock_filename)
            )

    def _release(self):
        if sys.platform == "win32":  # pragma: win32 cover
            fd = cast(int, self._lock_file_fd)
            self._lock_file_fd = None
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            os.close(fd)
            try:
                os.remove(self._lock_file)
            except OSError:
                pass
        else:
            import fcntl
            fd = cast(int, self._lock_file_fd)
            self._lock_file_fd = None
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            try:
                os.remove(self._lock_file)
            except OSError:  # pragma: no cover
                pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, _type, value, tb):
        self._release()

    def __del__(self) -> None:
        """Called when the lock object is deleted."""
        self.release()


def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


def check_pinned(self, posted=None):
    """
    Checks if a tweet is pinned and needs to be retrieved and posted on the
    Fediverse account
    """
    if posted is None:
        posted = {}
    # Only check pinned for 1 user
    t_user = self.twitter_username[0]

    logger.info(_(
        "Current pinned:\t{}"
    ).format(str(self.pinned_tweet_id)))
    pinned_file = os.path.join(self.user_path[t_user], "pinned_id.txt")
    if os.path.isfile(pinned_file):
        with open(pinned_file, "r") as file:
            previous_pinned_tweet_id = file.readline().rstrip()
            if previous_pinned_tweet_id == "":
                previous_pinned_tweet_id = None
    else:
        previous_pinned_tweet_id = None
    logger.info(
        _("Previous pinned:\t{}").format(str(previous_pinned_tweet_id))
    )
    if (
            self.pinned_tweet_id != previous_pinned_tweet_id
            and self.pinned_tweet_id is not None
    ):
        if self.pinned_tweet_id in posted:
            id_post_to_pin = posted[self.pinned_tweet_id]
        else:
            pinned_tweet = self._get_tweets("v2", self.pinned_tweet_id)
            tweets_to_post = {
                "data": [pinned_tweet["data"]],
                "includes": pinned_tweet["includes"],
            }
            tweets_to_post = self.process_tweets(tweets_to_post)
            id_post_to_pin = self.post(
                (
                    self.pinned_tweet_id,
                    tweets_to_post["data"][0]["text"],
                    pinned_tweet["data"]["created_at"],
                    tweets_to_post["data"][0]["reply_id"],
                    tweets_to_post["data"][0]["retweet_id"]
                ),
                tweets_to_post["data"][0]["polls"],
                tweets_to_post["data"][0]["possibly_sensitive"],
            )
        pinned_post = self.pin(id_post_to_pin)
        with open(pinned_file, "w") as file:
            file.write(f"{self.pinned_tweet_id}\n")
        if pinned_post is not None:
            with open(
                    os.path.join(
                        self.user_path[t_user],
                        "pinned_id_pleroma.txt"
                    ), "w"
            ) as file:
                file.write(f"{pinned_post}\n")
    elif (
            self.pinned_tweet_id != previous_pinned_tweet_id
            and previous_pinned_tweet_id is not None
    ):
        pinned_file = os.path.join(
            self.user_path[t_user],
            "pinned_id_pleroma.txt"
        )
        self.unpin(pinned_file)


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
        except (NameError, AttributeError):
            try:
                value = locals()[match.strip()]
            except (NameError, KeyError):
                value = globals()[match.strip()]
        if isinstance(value, list):
            value = ", ".join([str(elem) for elem in value])
        if isinstance(value, dict) or isinstance(value, CaseInsensitiveDict):
            if isinstance(self.twitter_username, list):
                for t_user in self.twitter_username:
                    dict_value = value[t_user]
                value = dict_value
            # value = json.dumps(value)
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


def _get_instance_info(self):
    try:
        nodeinfo_json = None
        nodeinfo_url = f"{self.pleroma_base_url}/.well-known/nodeinfo"
        response = requests.get(nodeinfo_url)
        if not response.ok:
            response.raise_for_status()
        nodeinfo = response.json()
        for lnk in nodeinfo["links"]:
            if lnk["rel"] == "http://nodeinfo.diaspora.software/ns/schema/2.0":
                nodeinfo_json_url = lnk["href"]
                response = requests.get(nodeinfo_json_url, headers={})
                if not response.ok:
                    response.raise_for_status()  # pragma
                nodeinfo_json = response.json()
                self.instance = nodeinfo_json["software"]["name"]
        if self.instance == "misskey":
            logger.info(_("Instance appears to be Misskey ฅ^•ﻌ•^ฅ"))
            if "metadata" in nodeinfo_json:
                metadata = nodeinfo_json["metadata"]
                self.max_post_length = metadata["maxNoteTextLength"]
                self.max_attachments = 16
    except (JSONDecodeError, requests.exceptions.HTTPError):
        msg = _("Instance response was not understood {}").format(
            response.text
        )
        raise ValueError(msg)
    if self.instance == "mastodon":
        logger.debug(_("Target instance is Mastodon..."))
        self.max_post_length = 500
        self.max_attachments = 4
        self.characters_reserved_per_url = 23
        self.max_video_attachments = 1
        instance_url = f"{self.pleroma_base_url}/api/v1/instance"
        response = requests.get(instance_url)
        instance_url_json = None
        if response.ok:
            instance_url_json = response.json()
        if (
                instance_url_json
                and "configuration" in instance_url_json
        ):  # pragma: todo
            if "statuses" in instance_url_json["configuration"]:
                statuses_conf = instance_url_json["configuration"]["statuses"]
                if "max_characters" in statuses_conf:
                    max_post_length = statuses_conf["max_characters"]
                    self.max_post_length = max_post_length
                if "max_media_attachments" in statuses_conf:
                    max_attachments = statuses_conf["max_media_attachments"]
                    self.max_attachments = max_attachments
                if "characters_reserved_per_url" in statuses_conf:
                    chars_url = statuses_conf["characters_reserved_per_url"]
                    self.characters_reserved_per_url = chars_url


def mastodon_enforce_limits(self):
    for t_user in self.twitter_username:
        if len(self.display_name[t_user]) > 30:
            self.display_name[t_user] = self.display_name[t_user][:30]
            log_msg = _(
                "Mastodon doesn't support display names longer than 30 "
                "characters, truncating it and trying again..."
            )
            logger.warning(log_msg)
    if hasattr(self, "rich_text"):
        if self.rich_text:
            self.rich_text = False
            logger.warning(
                _("Mastodon doesn't support rich text. Disabling it...")
            )


def _mastodon_len(self, text):  # pragma: todo
    # URI regex
    matching_pattern = (
        r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]"
        r"{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*"
        r"\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{}"
        r';:\'".,<>?«»“”‘’]))'
    )
    matches = re.finditer(matching_pattern, text)
    char_count_url = self.characters_reserved_per_url
    for matchNum, match in enumerate(matches, start=1):
        group = match.group()
        text = text.replace(group, group[:char_count_url])
    return len(text)


def force_date(self):
    logger.info(
        _("How far back should we retrieve tweets from the Twitter account?")
    )
    date_msg = _(
        "\nEnter a date (YYYY-MM-DD):"
        "\n[Leave it empty to retrieve *ALL* tweets or enter 'continue'"
        "\nif you want the bot to execute as normal (checking date of "
        "\nlast post in the Fediverse account)] "
    )
    logger.info(date_msg)
    input_date = input()
    if input_date == "continue":
        if self.posts != "none_found":
            date = self.get_date_last_post()
        else:
            date = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%dT%H:%M:%SZ"
            )
    elif input_date is None or input_date == "":
        self.max_tweets = 3200
        logger.warning(_("Raising max_tweets to the maximum allowed value"))
        # Minimum date allowed
        tw_oldest = "2006-07-15T00:00:00Z"
        tw_api_oldest = "2010-11-06T00:00:00Z"
        date = tw_oldest if self.archive else tw_api_oldest
    else:
        self.max_tweets = 3200
        logger.warning(_("Raising max_tweets to the maximum allowed value"))
        date = datetime.strftime(
            datetime.strptime(input_date, "%Y-%m-%d"),
            "%Y-%m-%dT%H:%M:%SZ",
        )
    return date


def check_date_format(self, input_date):
    match = False
    try:
        datetime.strptime(input_date, "%Y-%m-%d")
        match = True
    except ValueError:
        pass
    return match


def transform_date(self, input_date):
    date = datetime.strftime(
        datetime.strptime(input_date, "%Y-%m-%d"),
        "%Y-%m-%dT%H:%M:%SZ",
    )
    return date


def process_archive(self, archive_zip_path, start_time=None):
    from pleroma_bot._processing import _expand_urls

    archive_zip_path = os.path.abspath(archive_zip_path)
    par_dir = os.path.dirname(archive_zip_path)
    archive_name = os.path.basename(archive_zip_path).split('.')[0]
    extracted_dir = os.path.join(par_dir, archive_name)
    with zipfile.ZipFile(archive_zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_dir)
    tweet_js_path = os.path.join(extracted_dir, 'data', 'tweet.js')
    profile_js_path = os.path.join(extracted_dir, 'data', 'profile.js')
    account_js_path = os.path.join(extracted_dir, 'data', 'account.js')
    profile_info = _get_twitter_info_from_archive(profile_js_path)
    account_info = _get_account_info_from_archive(account_js_path)

    t_user = self.twitter_username[0]
    bio_text = profile_info["description"]["bio"]
    bio_text = self.replace_vars_in_str(str(self.bio_text))
    self.bio_text = {"_generic_bio_text": bio_text}
    if self.twitter_bio:
        bio_short = profile_info["description"]["bio"]
        bio = {'text': bio_short, 'entities': None}
        bio_long = _expand_urls(self, bio)
        max_len = self.max_post_length
        len_bio = len(f"{self.bio_text['_generic_bio_text']}{bio_long}")
        bio_text = bio_long if len_bio < max_len else bio_short
    self.bio_text[t_user] = (
        f"{self.bio_text['_generic_bio_text']}{bio_text}"
        if self.twitter_bio
        else f"{self.bio_text['_generic_bio_text']}"
    )
    self.website = profile_info["description"]["website"]
    website = {'text': self.website, 'entities': None}
    self.website = _expand_urls(self, website)
    self.display_name[t_user] = account_info["username"]
    self.twitter_ids[account_info["accountId"]] = account_info["username"]

    self.fields = self.replace_vars_in_str(str(self.fields))
    self.fields = eval(self.fields)

    a_end_id = ""
    h_end_id = ""
    if "avatarMediaUrl" in profile_info:
        a_end_id = profile_info["avatarMediaUrl"].split("/")[-1].split('.')[0]
    if "headerMediaUrl" in profile_info:
        h_end_id = profile_info["headerMediaUrl"].split("/")[-1].split('.')[0]

    profile_media_path = os.path.join(extracted_dir, 'data', 'profile_media')
    for media in os.listdir(profile_media_path):
        m_end_id = media.split("-")[-1].split('.')[0]
        if m_end_id == a_end_id:
            media_path = os.path.join(profile_media_path, media)
            self.profile_image_url[t_user] = media_path
            shutil.copy(media_path, self.avatar_path[t_user])
        if m_end_id == h_end_id:
            media_path = os.path.join(profile_media_path, media)
            self.profile_banner_url[t_user] = media_path
            shutil.copy(media_path, self.header_path[t_user])

    tweet_media_path = os.path.join(extracted_dir, 'data', 'tweet_media')
    # new archives filename
    if not os.path.isfile(tweet_js_path):
        tweet_js_path = os.path.join(extracted_dir, 'data', 'tweets.js')
    if not os.path.isdir(tweet_media_path):
        tweet_media_path = os.path.join(extracted_dir, 'data', 'tweets_media')
    tweets_archive = get_tweets_from_archive(tweet_js_path)
    tweets = {
        "data": [],
        "includes": {
            "users": [],
            "tweets": [],
            "media": [],
            "polls": []
        },
        "meta": {}
    }
    for tweet in tweets_archive:
        created_at = tweet["tweet"]["created_at"]
        created_at_f = datetime.strftime(
            datetime.strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y"),
            "%Y-%m-%dT%H:%M:%S.000Z",
        )
        if start_time:
            if created_at_f < start_time:
                continue
        tweet["tweet"]["text"] = tweet["tweet"]["full_text"]
        tweet["tweet"]["created_at"] = created_at_f
        if "possibly_sensitive" not in tweet["tweet"].keys():
            tweet["tweet"]["possibly_sensitive"] = False
        tweet_id = tweet["tweet"]["id"]
        tweet_media_dir = os.path.join(self.tweets_temp_path, tweet_id)
        if not os.path.isdir(tweet_media_dir):
            os.makedirs(tweet_media_dir, exist_ok=True)
        for media in os.listdir(tweet_media_path):
            if media.startswith(tweet_id):
                media_path = os.path.join(tweet_media_path, media)
                shutil.copy(media_path, tweet_media_dir)
        tweets["data"].append(tweet["tweet"])
    # Order it just in case
    tweets["data"] = sorted(
        tweets["data"], key=lambda i: i["created_at"], reverse=True
    )
    return tweets


def get_tweets_from_archive(tweet_js_path):
    with open(tweet_js_path, "r") as f:
        lines = []
        for line in f:
            line = re.sub(r'\n', r'', line)
            lines.append(line)
        tweets = '\n'.join(lines[1:-1])
    json_t = json.loads('{"tweets":[' + tweets + ']}')
    return json_t["tweets"]


def _get_twitter_info_from_archive(profile_js_path):
    with open(profile_js_path, "r") as f:
        lines = []
        for line in f:
            line = re.sub(r'\n', r'', line)
            lines.append(line)
        data = '\n'.join(lines[1:-1])
    json_p = json.loads(data)

    return json_p["profile"]


def _get_account_info_from_archive(account_js_path):
    with open(account_js_path, "r") as f:
        lines = []
        for line in f:
            line = re.sub(r'\n', r'', line)
            lines.append(line)
        data = '\n'.join(lines[1:-1])
    json_p = json.loads(data)

    return json_p["account"]


def post(self, tweet: tuple, poll: dict, sensitive, media=None) -> str:
    post_id = None
    instance = self.instance
    if media:
        media_id = 'id' if (self.archive or self.rss) else 'media_key'
        media = {
            key: [
                l_item for l_item in media if l_item[media_id] == key
            ] for key in set([i[media_id] for i in media])
        }
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        post_id = self.post_pleroma(tweet, poll, sensitive, media)
    elif self.instance == "misskey":
        post_id = self.post_misskey(tweet, poll, sensitive, media)
    return post_id


def pin(self, id_post):
    instance = self.instance
    pin_id = None
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        pin_id = self.pin_pleroma(id_post)
    elif instance == "misskey":
        pin_id = self.pin_misskey(id_post)
    return pin_id


def unpin(self, pinned_file):
    instance = self.instance
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        self.unpin_pleroma(pinned_file)
    elif instance == "misskey":
        self.unpin_misskey(pinned_file)


def get_date_last_post(self):
    instance = self.instance
    date = None
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        date = self.get_date_last_pleroma_post()
    elif instance == "misskey":
        date = self.get_date_last_misskey_post()
    elif instance == "cohost":  # pragma: todo
        date = self.get_date_last_cohost_post()
    return date


def update_profile(self):
    instance = self.instance
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        self.update_pleroma()
    elif instance == "misskey":
        self.update_misskey()


def random_id() -> str:  # pragma: todo
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(19)
    )


def parse_rss_feed(self, rss_link, start_time, threads=1):  # pragma: todo
    import feedparser
    if start_time:
        self.start_time = start_time
    tweets = {
        "data": [],
        "media_processed": [],
        "meta": []
    }
    d = feedparser.parse(rss_link)
    logger.info(_("Gathering tweets...{}").format(len(d.entries)))

    if threads > 1:
        dt = d.entries
        chunks = chunkify(dt, threads)
        with Pool(threads) as p:
            ret = []
            desc = _("Processing tweets... ")
            with tqdm(total=len(dt), desc=desc) as pbar:
                for idx, res in enumerate(
                        p.imap_unordered(
                            self._process_tweets_rss, chunks
                        )
                ):
                    pbar.update(len(chunks[idx]))
                    ret.append(res)

        tweets_merged = {
            "data": [],
            "meta": tweets["meta"],
            "media_processed": []
        }
        for idx in range(threads):
            tweets_merged["data"].extend(ret[idx]["data"])
            tweets_merged["media_processed"].extend(
                ret[idx]["media_processed"]
            )
        tweets_merged["data"] = sorted(
            tweets_merged["data"], key=lambda i: i["created_at"]
        )
        tweets = tweets_merged
    else:
        tweets = self._process_tweets_rss(d.entries)
    return tweets


def _process_tweets_rss(self, entries):  # pragma: todo
    start_time = self.start_time
    tweets = {
        "data": [],
        "media_processed": [],
        "meta": []
    }
    if self.threads == 1:
        desc = _("Processing tweets... ")
        pbar = tqdm(total=len(entries), desc=desc)
    for item in entries[:self.max_tweets]:
        created_at = datetime.strftime(
            datetime.strptime(item.published, "%a, %d %b %Y %H:%M:%S %Z"),
            "%Y-%m-%dT%H:%M:%S.000Z",
        )
        if start_time:
            if created_at < start_time:
                continue
        text = item.summary_detail.value
        warnings.filterwarnings(
            'ignore', category=MarkupResemblesLocatorWarning
        )
        soup = BeautifulSoup(text, "html.parser")
        soup_title = BeautifulSoup(item.title_detail.value, "html.parser")
        # Remove parent p tags if there are any
        if hasattr(soup.p, "unwrap"):
            soup.p.unwrap()
        # title_detail includes RT or reply header
        # but only summary_details includes links to media
        if not self.include_rts:
            if (
                    soup.prettify().startswith('RT ')
                    or soup_title.prettify().startswith('RT ')
            ):
                continue
        if not self.include_replies:
            if (
                    soup.prettify().startswith('@')
                    or soup.prettify().startswith('Re @')
                    or soup.prettify().startswith('R to @')
                    or soup_title.prettify().startswith('@')
                    or soup_title.prettify().startswith('Re @')
                    or soup_title.prettify().startswith('R to @')
            ):
                continue

        tweet_id = item.id.strip('#m').split('/')[-1]

        media = []
        for link in soup.find_all('a'):
            link.replace_with(f' {link.get("href")} ')

        for source in soup.find_all('source'):
            src = source.get('src')
            if src:
                media.append(
                    {
                        'url': src,
                        'type': 'rss',
                        'id': random_id()
                    }
                )
            source.replace_with('')
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                media.append(
                    {
                        'url': src,
                        'type': 'rss',
                        'id': random_id()
                    }
                )
            video.replace_with('')
        for image in soup.find_all('img'):
            src = image.get('src')
            if src:
                media.append(
                    {
                        'url': src,
                        'type': 'rss',
                        'id': random_id()
                    }
                )
            image.replace_with('')
        for br in soup.find_all('br'):
            br.replace_with('\n')
        if (
                (
                    soup_title.prettify().startswith('RT ')
                    or soup_title.prettify().startswith('@')
                    or soup_title.prettify().startswith('Re @')
                    or soup_title.prettify().startswith('R to @')
                )
                and not (
                    soup_title.prettify().endswith('...')
                    or soup_title.prettify().endswith('…')
                    or soup_title.prettify().endswith('...\n')
                    or soup.prettify().startswith('RT ')
                    or soup.prettify().startswith('@')
                    or soup.prettify().startswith('Re @')
                    or soup.prettify().startswith('R to @')
                )
        ):
            tweet_text = soup_title.prettify()
        else:
            tweet_text = soup.prettify()
        tweet = {"text": tweet_text, "created_at": created_at}
        if hasattr(self, "rich_text"):
            if self.rich_text:
                tweet["text"] = self._replace_mentions(tweet)

        if self.invidious:
            tweet["text"] = self._replace_url(
                tweet["text"],
                "https://youtube.com",
                self.invidious_base_url
            )
        signature = ''
        if self.signature:
            signature = f"\n\n 🐦🔗: {item.link}"
            total_length = len(tweet["text"]) + len(signature)
            if total_length > self.max_post_length:  # pragma
                body_max_length = self.max_post_length - len(signature) - 1
                tweet["text"] = f"{tweet['text'][:body_max_length]}…"
            tweet["text"] = f"{tweet['text']}{signature}"
        if self.nitter:
            tweet["text"] = self._replace_url(
                tweet["text"],
                "https://twitter.com",
                self.nitter_base_url
            )
        if self.original_date:
            tweet_date = tweet["created_at"]
            date = datetime.strftime(
                datetime.strptime(tweet_date, "%Y-%m-%dT%H:%M:%S.000Z"),
                self.original_date_format,
            )
            orig_date = f"\n\n[{date}]"
            total_length = len(tweet["text"]) + len(orig_date)
            if total_length > self.max_post_length:  # pragma
                if self.signature:
                    tweet["text"] = tweet["text"].replace(signature, '')
                l_date = len(orig_date)
                l_sig = len(signature)
                body_max_length = self.max_post_length - l_date - l_sig - 1
                tweet["text"] = f"{tweet['text'][:body_max_length]}…"
            else:
                signature = ''
            tweet["text"] = f"{tweet['text']}{signature}{orig_date}"
        # Truncate text if needed
        if len(tweet["text"]) > self.max_post_length:  # pragma
            logger.info(
                _(
                    "Post text longer than allowed ({}), truncating..."
                ).format(self.max_post_length)
            )
            tweet["text"] = f"{tweet['text'][:self.max_post_length]}"

        data = {
            'id': tweet_id,
            'created_at': created_at,
            'text': tweet["text"],
            'author_id': item.author,
            'possibly_sensitive': False,
            'polls': []
        }

        tweets["data"].append(data)
        if self.media_upload:
            if len(media) > 0:
                tweet_path = os.path.join(self.tweets_temp_path, tweet_id)
                os.makedirs(tweet_path, exist_ok=True)
                self._download_media(media, data)
                tweets["media_processed"].extend(media)
        if self.threads == 1:
            pbar.update(1)
    return tweets


def _update_bot_status(self, bot):  # pragma: todo
    instance = self.instance
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        self._pleroma_update_bot_status(bot)
    elif instance == "misskey":
        self._misskey_update_bot_status(bot)


def _get_fedi_profile_info(self):  # pragma: todo
    instance = self.instance
    if instance == "mastodon" or instance == "pleroma" or instance is None:
        fedi_profile = self._get_pleroma_profile_info()
    elif instance == "misskey":
        fedi_profile = self._get_misskey_profile_info()
    else:
        fedi_profile = None
    if hasattr(self, "bot"):
        fedi_bot = self.bot
        if "bot" in fedi_profile:
            fedi_bot = fedi_profile["bot"]
        if fedi_bot is not self.bot:
            msg = _(
                "Bot flag in target profile ({}) differs from your config. "
                "Updating it to {}... "
            ).format(fedi_bot, self.bot)
            logger.warning(msg)
            self._update_bot_status(self.bot)


def _get_fedi_info(self):  # pragma: todo
    self._get_fedi_profile_info()


def _get_guest_token_header(self):  # pragma: todo
    _guest_token = (
        "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7tt"
        "fk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    )
    guest_url = f"{self.twitter_base_url}/guest/activate.json"
    headers = {"Authorization": f"Bearer {_guest_token}"}
    user_agent = (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        f" like Gecko) Chrome/79.0.3945.{random.randint(0, 9999)} Safari/537."
        f"{random.randint(0, 99)}"
    )
    headers['User-Agent'] = user_agent
    headers.update({"user-agent": user_agent})
    response = requests.post(guest_url, headers=headers, stream=True)
    if not response.ok:
        if self.proxy and response.status_code == 429:
            logger.warning(
                _(
                    "Rate limit exceeded when getting guest token. Retrying "
                    "with a proxy."
                )
            )
            response = self._request_proxy(
                method='POST', url=guest_url, headers=headers
            )
        else:
            response.raise_for_status()
    json_resp = response.json()
    guest_token = json_resp['guest_token']
    headers.update({"x-guest-token": guest_token})

    headers.update({
        "accept": "*/*",
        "accept-language": "de,en-US;q=0.7,en;q=0.3",
        "accept-encoding": "gzip, deflate, utf-8",
        "te": "trailers",
    })
    return _guest_token, headers


def _request_proxy(
        self, method, url,
        params=None, data=None, headers=None, cookies=None,
        files=None, auth=None, timeout=None, proxies=None,
        hooks=None, allow_redirects=True, stream=None,
        verify=None, cert=None, json=None
):  # pragma: todo
    if not self.pool_iter:
        response = requests.get('https://www.sslproxies.org/')
        matches = re.findall(
            r"<td>\d+.\d+.\d+.\d+</td><td>\d+</td>", response.text
        )
        entries = [m.replace('<td>', '') for m in matches]
        proxies = [s[:-5].replace('</td>', ':') for s in entries]
        self.pool_iter = cycle(proxies)
    for i in range(100):
        proxy = next(self.pool_iter)
        try:
            logger.info(_("Trying {}").format(proxy))
            proxies = {
                "http": 'http://' + proxy,
                "https": 'http://' + proxy
            }
            response = requests.request(
                method,
                url,
                data=data or {},
                json=json,
                params=params or {},
                headers=headers,
                cookies=cookies, files=files,
                auth=auth, hooks=hooks,
                proxies=proxies,
                allow_redirects=allow_redirects,
                stream=stream, verify=verify,
                cert=cert,
                timeout=5.0
            )
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(e)
            continue
