import os
from json.decoder import JSONDecodeError

import json
import requests

from . import logger
from .i18n import _


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

    pinned_file = os.path.join(self.user_path[t_user], "pinned_id_pleroma.txt")
    self.unpin_pleroma(pinned_file)

    pin_url = f"{self.pleroma_base_url}/api/v1/statuses/{id_post}/pin"
    response = requests.post(pin_url, headers=self.header_pleroma)
    logger.info(_("Pinning post:\t{}").format(str(response.text)))
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
        logger.info(_("Unpinning previous:\t{}").format(response.text))
    else:
        logger.info(
            _(
                "File with previous pinned post ID not found or empty. "
                "Checking last posts for pinned post..."
            )
        )
        _find_pinned(self, pinned_file)
        logger.warning(_("Pinned post not found. Giving up unpinning..."))
    # Clear pinned ids
    with open(pinned_file, "w") as file:
        file.write("\n")
    with open(pinned_file_twitter, "w") as file:
        file.write("\n")


def _find_pinned(self, pinned_file):
    page = 0
    headers_page_url = None
    while page < 10:
        if self.posts:
            for post in self.posts:
                if post["pinned"]:
                    with open(pinned_file, "w") as file:
                        file.write(f'{post["id"]}\n')
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
        response = requests.get(statuses_url, headers=self.header_pleroma)
        if not response.ok:
            response.raise_for_status()
        posts = json.loads(response.text)
        self.posts = posts
        try:
            links = requests.utils.parse_header_links(
                response.headers["link"].rstrip(">").replace(">,<", ",<")
            )
            for link in links:
                if link["rel"] == "next":
                    headers_page_url = link["url"]
        except KeyError:
            break


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
    response = requests.get(
        url, headers=self.header_twitter, params=params, auth=self.auth
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
