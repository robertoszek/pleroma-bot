import os
import re
import sys
import time
import json
import string
import random
import zipfile
import tempfile
import requests
import threading
import functools
import mimetypes

from typing import cast
from errno import ENOENT
from itertools import cycle
from multiprocessing import Queue
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
from itertools import tee, islice, chain
from requests.structures import CaseInsensitiveDict

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


def spinner(message, wait: float = 0.3, spinner_symbols: list = None):
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
    mp = Multiprocessor()
    for idx in range(threads):
        tweets_chunked = {
            "data": chunks[idx],
            "includes": tweets["includes"],
            "meta": tweets["meta"]
        }
        mp.run(user.process_tweets, tweets_chunked)
    ret = mp.wait()  # get all results
    tweets_merged = {
        "data": [],
        "includes": tweets["includes"],
        "meta": tweets["meta"]
    }
    for idx in range(threads):
        tweets_merged["data"].extend(ret[idx]["data"])
    tweets_merged["data"] = sorted(
        tweets_merged["data"], key=lambda i: i["created_at"]
    )
    return tweets_merged


class Multiprocessor:

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

    @spinner(_("Processing tweets... "), 1.2)
    def wait(self):
        rets = []
        for p in self.processes:
            ret = self.queue.get()
            rets.append(ret)
        for p in self.processes:
            p.join()
        return rets


class PropagatingThread(threading.Thread):
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
    def __init__(self, timeout=5):
        module_name = __loader__.name.split('.')[0]
        lock_filename = f"{module_name}.lock"
        self.timeout = timeout
        self.tmp = tempfile.gettempdir()
        self.mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        self._lock_file = os.path.join(self.tmp, lock_filename)
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


def check_pinned(self):
    """
    Checks if a tweet is pinned and needs to be retrieved and posted on the
    Fediverse account
    """
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
        pinned_tweet = self._get_tweets("v2", self.pinned_tweet_id)
        tweets_to_post = {
            "data": [pinned_tweet["data"]],
            "includes": pinned_tweet["includes"],
        }
        tweets_to_post = self.process_tweets(tweets_to_post)
        id_post_to_pin = self.post_pleroma(
            (
                self.pinned_tweet_id,
                tweets_to_post["data"][0]["text"],
                pinned_tweet["data"]["created_at"],
            ),
            tweets_to_post["data"][0]["polls"],
            tweets_to_post["data"][0]["possibly_sensitive"],
        )
        pleroma_pinned_post = self.pin_pleroma(id_post_to_pin)
        with open(pinned_file, "w") as file:
            file.write(f"{self.pinned_tweet_id}\n")
        if pleroma_pinned_post is not None:
            with open(
                    os.path.join(
                        self.user_path[t_user],
                        "pinned_id_pleroma.txt"
                    ), "w"
            ) as file:
                file.write(f"{pleroma_pinned_post}\n")
    elif (
            self.pinned_tweet_id != previous_pinned_tweet_id
            and previous_pinned_tweet_id is not None
    ):
        pinned_file = os.path.join(
            self.user_path[t_user],
            "pinned_id_pleroma.txt"
        )
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
    instance_url = f"{self.pleroma_base_url}/api/v1/instance"
    response = requests.get(instance_url)
    if not response.ok:
        response.raise_for_status()
    try:
        instance_info = json.loads(response.text)
    except JSONDecodeError:
        msg = _("Instance response was not understood {}").format(
            response.text
        )
        raise ValueError(msg)
    if "Pleroma" not in instance_info["version"]:
        logger.debug(_("Assuming target instance is Mastodon..."))
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
            date = self.get_date_last_pleroma_post()
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


def process_archive(archive_zip_path, start_time=None):
    archive_zip_path = os.path.abspath(archive_zip_path)
    par_dir = os.path.dirname(archive_zip_path)
    archive_name = os.path.basename(archive_zip_path).split('.')[0]
    extracted_dir = os.path.join(par_dir, archive_name)
    with zipfile.ZipFile(archive_zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_dir)
    tweet_js_path = os.path.join(extracted_dir, 'data', 'tweet.js')
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
            "%Y-%m-%dT%H:%M:%SZ",
        )
        if start_time:
            if created_at_f < start_time:
                continue
        tweet["tweet"]["text"] = tweet["tweet"]["full_text"]
        tweet["tweet"]["created_at"] = created_at_f
        if "possibly_sensitive" not in tweet["tweet"].keys():
            tweet["tweet"]["possibly_sensitive"] = False
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
