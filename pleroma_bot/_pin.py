import os
from json.decoder import JSONDecodeError

import json
import requests

from . import logger
from .i18n import _
from pleroma_bot._twitter import twitter_api_request


def pin_misskey(self, id_post):
    """Tries to unpin previous pinned post if a file containing the ID
       of the previous post exists, then proceeds to pin the post
       with ID 'id_post'

       :param id_post: ID of post to pin
       :returns: ID of post pinned
       :rtype: str
       """
    # Only check pinned for 1 user
    t_user = self.twitter_username[0]
    filename = f"pinned_id_{self.instance}.txt"
    pinned_file = os.path.join(self.user_path[t_user], filename)
    self.unpin_misskey(pinned_file)

    pin_url = f"{self.pleroma_base_url}/api/i/pin"
    data = {
        "i": self.pleroma_token,
        "noteId": id_post
    }
    response = requests.post(
        pin_url, json.dumps(data), headers=self.header_pleroma
    )
    logger.info(_("Pinning post:\t{}").format(response))
    try:
        pin_id = json.loads(response.text)["id"]
    except KeyError:
        pin_id = None
        pass
    return pin_id


def unpin_misskey(self, pinned_file):
    """
    Unpins post with the ID stored in the file passed as parameter
    :param pinned_file: path to file containing post ID

    """
    # Only check pinned for 1 user
    t_user = self.twitter_username[0]

    pinned_file_twitter = os.path.join(self.user_path[t_user], "pinned_id.txt")
    previous_pinned_post_id = None
    if os.path.isfile(pinned_file):
        with open(os.path.join(pinned_file), "r") as file:
            previous_pinned_post_id = file.readline().rstrip()
            if previous_pinned_post_id == "":
                previous_pinned_post_id = None

    if previous_pinned_post_id:
        unpin_url = f"{self.pleroma_base_url}/api/i/unpin"
        data = {
            "noteId": previous_pinned_post_id,
            "i": self.pleroma_token
        }
        headers = {"Content-Type": "text/plain;charset=UTF-8"}
        response = requests.post(
            unpin_url, json.dumps(data), headers=headers
        )
        if not response.ok:
            response.raise_for_status()
        logger.info(_("Unpinning previous:\t{}").format(response))
    else:
        logger.info(
            _(
                "File with previous pinned post ID not found or empty. "
                "Checking last posts for pinned post..."
            )
        )
        pinned = _find_pinned_misskey(self, pinned_file)
        if pinned:
            unpinned = ' '.join(map(str, pinned))
            logger.info(_("Unpinned: {}").format(unpinned))
        else:  # pragma
            logger.warning(_("Pinned post not found. Giving up unpinning..."))
    # Clear pinned ids
    with open(pinned_file, "w") as file:
        file.write("\n")
    with open(pinned_file_twitter, "w") as file:
        file.write("\n")


def _find_pinned_misskey(self, pinned_file):
    i_url = f"{self.pleroma_base_url}/api/i"
    data = {"i": self.pleroma_token}
    response = requests.post(
        i_url, json.dumps(data), headers=self.header_pleroma
    )
    i_id = response.json()["id"]
    data = {
        "userId": i_id,
        "includeReplies": True,
        # "sinceId": ,
        "limit": 100,
        "includeMyRenotes": True,
    }
    users_url = f"{self.pleroma_base_url}/api/users/show"
    response = requests.post(
        users_url, json.dumps(data), headers=self.header_pleroma
    )
    users_show = response.json()
    for post_id in users_show["pinnedNoteIds"]:
        with open(pinned_file, "w") as file:
            file.write(f'{post_id}\n')
        self.unpin_misskey(pinned_file)
    return users_show["pinnedNoteIds"]


def pin_pleroma(self, id_post):
    """Tries to unpin previous pinned post if a file containing the ID
    of the previous post exists, then proceeds to pin the post
    with ID 'id_post'

    :param id_post: ID of post to pin
    :returns: ID of post pinned
    :rtype: str
    """
    # Only check pinned for 1 user
    t_user = self.twitter_username[0]
    filename = f"pinned_id_{self.instance}.txt"
    pinned_file = os.path.join(self.user_path[t_user], filename)
    self.unpin_pleroma(pinned_file)

    pin_url = f"{self.pleroma_base_url}/api/v1/statuses/{id_post}/pin"
    response = requests.post(pin_url, headers=self.header_pleroma)
    logger.info(_("Pinning post:\t{}").format(response))
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
    # Only check pinned for 1 user
    t_user = self.twitter_username[0]

    pinned_file_twitter = os.path.join(self.user_path[t_user], "pinned_id.txt")
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
        logger.info(_("Unpinning previous:\t{}").format(response))
    else:
        logger.info(
            _(
                "File with previous pinned post ID not found or empty. "
                "Checking last posts for pinned post..."
            )
        )
        pinned = _find_pinned(self, pinned_file)
        if pinned:
            unpinned = ' '.join(map(str, pinned))
            logger.info(_("Unpinned: {}").format(unpinned))
        else:
            logger.warning(_("Pinned post not found. Giving up unpinning..."))
    # Clear pinned ids
    with open(pinned_file, "w") as file:
        file.write("\n")
    with open(pinned_file_twitter, "w") as file:
        file.write("\n")


def _find_pinned(self, pinned_file):
    page = 0
    headers_page_url = None
    pinned = []
    if self.posts != "none_found":
        while page < 10:
            try:
                if self.posts:
                    for post in self.posts:
                        if post["pinned"]:
                            pinned.append(post["id"])
                            with open(pinned_file, "w") as file:
                                file.write(f'{post["id"]}\n')
                            self.unpin_pleroma(pinned_file)
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
            except KeyError:
                break
    return pinned


def _get_pinned_tweet_id(self):
    """Retrieves the pinned tweet by the user

    :returns: ID of currently pinned tweet
    """
    # Only get pin for 1 user
    t_user = self.twitter_username[0]

    url = (
        f"{self.twitter_base_url_v2}/users/"
        f"by/username/{t_user}"
    )
    params = {
        "user.fields": "pinned_tweet_id",
        "expansions": "pinned_tweet_id",
        "tweet.fields": "entities",
    }
    response = twitter_api_request(
        'GET', url, headers=self.header_twitter, params=params, auth=self.auth
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


def get_pinned_tweet(self):
    return self.pinned_tweet_id
