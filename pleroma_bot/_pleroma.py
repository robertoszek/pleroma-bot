import os
from json.decoder import JSONDecodeError

import re
import json
import time
import shutil
import requests
import mimetypes
from datetime import datetime, timedelta, timezone

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from . import logger
from .i18n import _
from ._utils import random_string, guess_type


def pleroma_api_request(method, url,
                        params=None, data=None, headers=None, cookies=None,
                        files=None, auth=None, timeout=None, proxies=None,
                        hooks=None, allow_redirects=True, stream=None,
                        verify=None, cert=None, json=None):  # pragma: todo
    response = requests.request(
        method=method.upper(),
        url=url,
        headers=headers,
        files=files,
        data=data or {},
        json=json,
        params=params or {},
        auth=auth,
        cookies=cookies,
        hooks=hooks,
    )
    if response.status_code == 429:
        remaining_header = response.headers.get("X-RateLimit-Remaining")
        limit_header = response.headers.get("X-RateLimit-Limit")
        reset_header = response.headers.get("X-RateLimit-Reset")
        if remaining_header and limit_header and reset_header:
            remaining = int(remaining_header)
            limit = int(limit_header)
            ts = datetime.strptime(
                reset_header,
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc).timestamp()
            reset_time = datetime.utcfromtimestamp(ts)

            logger.info(_(
                "Rate limit exceeded. {} out of {} requests remaining until {}"
                " UTC"
            ).format(remaining, limit, reset_time))

            delay = (reset_time - datetime.utcnow()).total_seconds() + 2
            logger.info(_("Sleeping for {}s...").format(round(delay)))
            time.sleep(delay)

            response = pleroma_api_request(method, url,
                                           params=params, data=data,
                                           headers=headers, cookies=cookies,
                                           files=files, auth=auth, hooks=hooks,
                                           timeout=timeout, proxies=proxies,
                                           allow_redirects=allow_redirects,
                                           stream=stream, verify=verify,
                                           cert=cert, json=json)
    return response


def get_date_last_pleroma_post(self):
    """Gathers last post from the user in Pleroma and returns the date
    of creation.

    :returns: Date of last Pleroma post in '%Y-%m-%dT%H:%M:%SZ' format
    """
    pleroma_posts_url = (
        f"{self.pleroma_base_url}/api/v1/accounts/"
        f"{self.pleroma_username}/statuses"
    )
    response = pleroma_api_request(
        'GET',
        pleroma_posts_url,
        headers=self.header_pleroma,
    )
    if not response.ok:
        response.raise_for_status()
    posts = json.loads(response.text)
    self.posts = posts
    if posts:
        date_pleroma = posts[0]["created_at"]
    else:
        self.posts = "none_found"
        logger.warning(
            _("No posts were found in the target Fediverse account")
        )
        if self.first_time:
            date_pleroma = self.force_date()
        else:
            date_pleroma = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%dT%H:%M:%SZ"
            )

    return date_pleroma


def post_pleroma(
        self,
        tweet: tuple,
        poll: dict,
        sensitive: bool,
        media: list = None
) -> str:
    """Post the given text to the Pleroma instance associated with the
    User object

    :param media: List containing media metadata
    :param tweet: Tuple containing tweet_id, tweet_text. The ID will be used to
    link to the Twitter status if 'signature' is True and to find related media
    tweet_text is the literal text to use when creating the post.
    :type tweet: tuple
    :param poll: dict of poll if attached to tweet
    :type poll: dict
    :param sensitive: if tweet is possibly sensitive or not
    :type sensitive: bool
    :returns: id of post
    :rtype: str
    """
    post_id = None
    pleroma_post_url = f"{self.pleroma_base_url}/api/v1/statuses"
    pleroma_media_url = f"{self.pleroma_base_url}/api/v1/media"

    tweet_id, tweet_text, tweet_date, tweet_reply_id, retweet_id = tweet
    tweet_folder = os.path.join(self.tweets_temp_path, tweet_id)

    posts = self.posts_ids[self.pleroma_base_url]
    if (
            tweet_id in posts
            and len(str(posts[tweet_id])) > 0
            and self.avoid_duplicates
    ):  # pragma: todo
        post_id = self.posts_ids[self.pleroma_base_url][tweet_id]
        pleroma_posted_url = (
            f"{self.pleroma_base_url}/api/v1/statuses/{post_id}"
        )
        response = pleroma_api_request(
            'GET',
            pleroma_posted_url,
            headers=self.header_pleroma,
        )
        if response.ok:
            logger.warning(
                _(
                    "Tweet already posted in Pleroma:\t{} - {}."
                    " Skipping to avoid duplicates..."
                ).format(tweet_id, posts[tweet_id])
            )
            return post_id

    if (
            retweet_id
            and retweet_id in posts
            and len(str(posts[retweet_id])) > 0
    ):  # pragma: todo
        post_id = self.posts_ids[self.pleroma_base_url][retweet_id]
        pleroma_reblog_url = (
            f"{self.pleroma_base_url}/api/v1/statuses/{post_id}/reblog"
        )
        response = pleroma_api_request(
            'POST',
            pleroma_reblog_url,
            headers=self.header_pleroma,
        )
        if not response.ok:
            response.raise_for_status()
        logger.debug(_("Reblog in Pleroma:\t{}").format(str(response)))
        return post_id

    media_ids = []
    video_ids = []
    if self.media_upload:
        tweet_video_count = 0
        if os.path.isdir(tweet_folder):
            media_files = sorted(os.listdir(tweet_folder))
            for file in media_files:
                # for file in media_files:
                file_path = os.path.join(tweet_folder, file)
                media_file = open(file_path, "rb")
                file_size = os.stat(os.path.join(tweet_folder, file)).st_size
                size_mb = round(file_size / 1048576, 2)
                alt_text = None
                if media:
                    key = file.split("-")[1].split(".")[0]
                    item = media[key][0]
                    alt_text = item["alt_text"] if "alt_text" in item else None
                mime_type = guess_type(os.path.join(tweet_folder, file))
                if (
                        mime_type.startswith("video")
                        and self.max_video_attachments
                ):  # pragma: todo
                    tweet_video_count += 1
                    if tweet_video_count > self.max_video_attachments:
                        logger.warning(
                            _(
                                "Mastodon only supports 1 video per post. "
                                "Already reached max media,"
                                " skipping the rest... "
                            )
                        )
                        continue
                timestamp = int(float(datetime.now().timestamp()))
                file_name = (
                    f"pleromapyupload_"
                    f"{timestamp}"
                    f"_"
                    f"{random_string(10)}"
                    f"{mimetypes.guess_extension(mime_type)}"
                )
                file_description = (file_name, media_file, mime_type)
                files = {"file": file_description}
                data = {}
                if alt_text:  # pragma
                    data.update(
                        {
                            "description": alt_text
                        }
                    )
                response = pleroma_api_request(
                    'POST',
                    pleroma_media_url,
                    data=data,
                    headers=self.header_pleroma,
                    files=files
                )
                try:
                    if not response.ok:
                        response.raise_for_status()
                except requests.exceptions.HTTPError:
                    if response.status_code == 413:
                        size_msg = _(
                            "Exception occurred"
                            "\nMedia size too large:"
                            "\nFilename: {file}"
                            "\nSize: {size}MB"
                            "\nConsider increasing the attachment"
                            "\n size limit of your instance"
                        ).format(file=file_path, size=size_mb)
                        logger.error(size_msg)
                        pass
                    elif response.status_code == 422:
                        error = ""
                        response_msg = json.loads(response.text)
                        if "error" in response_msg:
                            error = response_msg["error"]
                        validation_msg = _(
                            "Exception occurred"
                            "\nUnprocessable Entity"
                            "\n{error}"
                            "\nFile: {file}"
                        ).format(error=error, file=file_path)
                        logger.error(validation_msg)
                        pass
                    else:
                        response.raise_for_status()
                try:
                    media_id = json.loads(response.text)["id"]
                    media_ids.append(media_id)
                    if (
                            self.instance == "mastodon"
                            and mime_type.startswith("video")
                    ):  # pragma: todo
                        video_ids.append(media_id)
                except (KeyError, JSONDecodeError):
                    logger.warning(
                        _("Error uploading media:\t{}").format(
                            response.status_code
                        )
                    )
                    pass
    # remove video or rest of media if mixed with other media for mastodon
    if self.instance == "mastodon":  # pragma: todo
        for video_id in video_ids:
            if video_id in media_ids:
                idx = media_ids.index(video_id)
                if idx > 0 and len(media_ids) > 1:
                    logger.warning(
                        _(
                            "Mastodon cannot attach a video to a post that "
                            "already contains images, "
                            "skipping the rest of media... "
                        )
                    )
                    media_ids.remove(video_id)
                if idx == 0 and len(media_ids) > 1:
                    logger.warning(
                        _(
                            "Mastodon only supports 1 video per post. "
                            "Already reached max media,"
                            " skipping the rest... "
                        )
                    )
                    media_ids = media_ids[:1]
    # config setting override tweet attr
    if self.sensitive:
        sensitive = self.sensitive

    data = {
        "status": tweet_text,
        "sensitive": str(sensitive).lower(),
        "visibility": self.visibility,
        "media_ids[]": media_ids,
    }
    if (
            tweet_reply_id
            and tweet_reply_id in posts
            and len(str(posts[tweet_reply_id])) > 0
    ):  # pragma: todo
        post_reply_id = self.posts_ids[self.pleroma_base_url][tweet_reply_id]
        data.update({"in_reply_to_id": post_reply_id})
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

    empty = (tweet_text == '' and len(media_ids) == 0 and poll is None)
    if not empty:
        response = pleroma_api_request(
            'POST',
            pleroma_post_url,
            data=data,
            headers=self.header_pleroma,
        )
        if not response.ok:
            response.raise_for_status()
        logger.debug(_("Post in Pleroma:\t{}").format(str(response)))
        post_id = json.loads(response.text)["id"]
        self.posts_ids[self.pleroma_base_url].update({tweet_id: post_id})
    return post_id


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
    # Only update 1 user
    t_user = self.twitter_username[0]
    if not self.archive:
        # Get the biggest resolution for the profile picture (400x400)
        # instead of 'normal'
        if t_user in self.profile_image_url:
            profile_img_big = re.sub(
                r"normal", "400x400",
                self.profile_image_url[t_user]
            )
            response = requests.get(profile_img_big, stream=True)
            if not response.ok:
                response.raise_for_status()
            response.raw.decode_content = True
            with open(self.avatar_path[t_user], "wb") as outfile:
                shutil.copyfileobj(response.raw, outfile)

        if t_user in self.profile_banner_url:
            response = requests.get(
                self.profile_banner_url[t_user], stream=True
            )
            if not response.ok:
                response.raise_for_status()
            response.raw.decode_content = True
            with open(self.header_path[t_user], "wb") as outfile:
                shutil.copyfileobj(response.raw, outfile)

    # Set it on Pleroma
    cred_url = f"{self.pleroma_base_url}/api/v1/accounts/update_credentials"

    # Construct fields
    fields = []
    for field_item in self.fields:
        field = (field_item["name"], field_item["value"])
        fields.append(field)
    data = {
        "note": self.bio_text[t_user],
        "display_name": self.display_name[t_user]
    }

    if t_user in self.profile_image_url:
        data.update({"avatar": self.avatar_path[t_user]})

    if t_user in self.profile_banner_url:
        data.update({"header": self.header_path[t_user]})

    if len(fields) > 4:
        raise Exception(
            _(
                "Total number of metadata fields cannot exceed 4."
                "\nProvided: {}. Exiting..."
            ).format(len(fields))
        )
    for idx, (field_name, field_value) in enumerate(fields):
        data[f'fields_attributes["{str(idx)}"][name]'] = field_name
        data[f'fields_attributes["{str(idx)}"][value]'] = field_value

    files = {}
    timestamp = str(datetime.now().timestamp())
    if t_user in self.profile_image_url:
        avatar = open(self.avatar_path[t_user], "rb")
        avatar_mime_type = guess_type(self.avatar_path[t_user])
        avatar_file_name = (
            f"pleromapyupload_{timestamp}_"
            f"{random_string(10)}"
            f"{mimetypes.guess_extension(avatar_mime_type)}"
        )
        files.update({"avatar": (avatar_file_name, avatar, avatar_mime_type)})
    if t_user in self.profile_banner_url:
        header = open(self.header_path[t_user], "rb")
        header_mime_type = guess_type(self.header_path[t_user])
        header_file_name = (
            f"pleromapyupload_{timestamp}_"
            f"{random_string(10)}"
            f"{mimetypes.guess_extension(header_mime_type)}"
        )
        files.update({"header": (header_file_name, header, header_mime_type)})

    response = pleroma_api_request(
        'PATCH',
        cred_url,
        data=data,
        headers=self.header_pleroma,
        files=files
    )
    try:
        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 422:
            bio_msg = _(
                "Exception occurred"
                "\nError code 422"
                "\n(Unprocessable Entity)"
                "\nPlease check that the bio text or the metadata fields text"
                "\naren't too long."
            )
            logger.error(bio_msg)
            pass
        else:
            response.raise_for_status()
    logger.info(_("Updating profile:\t {}").format(str(response)))
    return


def _pleroma_update_bot_status(self, bot):  # pragma: todo
    update_cred_url = (
        f"{self.pleroma_base_url}/api/v1/accounts/update_credentials"
    )
    data = {"bot": str(bot).lower()}
    response = pleroma_api_request(
        'PATCH',
        update_cred_url,
        data=data,
        headers=self.header_pleroma,
    )
    if not response.ok:
        response.raise_for_status()


def _get_pleroma_profile_info(self):  # pragma: todo
    profile_url = (
        f"{self.pleroma_base_url}/api/v1/accounts/"
        f"{self.pleroma_username}"
    )
    response = pleroma_api_request(
        'GET',
        profile_url,
        headers=self.header_pleroma,
    )
    if not response.ok:
        response.raise_for_status()
    profile = response.json()
    return profile
