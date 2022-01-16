import os
from json.decoder import JSONDecodeError

import re
import json
import shutil
import requests
import mimetypes
from datetime import datetime, timedelta

# Try to import libmagic
# if it fails just use mimetypes
try:
    import magic
except ImportError:
    magic = None

from . import logger
from .i18n import _
from ._utils import random_string, guess_type


def get_date_last_pleroma_post(self):
    """Gathers last post from the user in Pleroma and returns the date
    of creation.

    :returns: Date of last Pleroma post in '%Y-%m-%dT%H:%M:%SZ' format
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


def post_pleroma(self, tweet: tuple, poll: dict, sensitive: bool) -> str:
    """Post the given text to the Pleroma instance associated with the
    User object

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

    pleroma_post_url = f"{self.pleroma_base_url}/api/v1/statuses"
    pleroma_media_url = f"{self.pleroma_base_url}/api/v1/media"

    tweet_id, tweet_text, tweet_date = tweet
    tweet_folder = os.path.join(self.tweets_temp_path, tweet_id)

    media_ids = []
    if self.media_upload:
        if os.path.isdir(tweet_folder):
            media_files = os.listdir(tweet_folder)
            for file in media_files:
                file_path = os.path.join(tweet_folder, file)
                media_file = open(file_path, "rb")
                file_size = os.stat(os.path.join(tweet_folder, file)).st_size
                size_mb = round(file_size / 1048576, 2)

                mime_type = guess_type(os.path.join(tweet_folder, file))
                timestamp = str(datetime.now().timestamp())
                file_name = (
                    f"pleromapyupload_"
                    f"{timestamp}"
                    f"_"
                    f"{random_string(10)}"
                    f"{mimetypes.guess_extension(mime_type)}"
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
                    else:
                        response.raise_for_status()
                try:
                    media_ids.append(json.loads(response.text)["id"])
                except (KeyError, JSONDecodeError):
                    logger.warning(
                        _("Error uploading media:\t{}").format(
                            str(response.text)
                        )
                    )
                    pass

    # config setting override tweet attr
    if self.sensitive:
        sensitive = self.sensitive

    data = {
        "status": tweet_text,
        "sensitive": str(sensitive).lower(),
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
    logger.info(_("Post in Pleroma:\t{}").format(str(response)))
    post_id = json.loads(response.text)["id"]
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
    # Get the biggest resolution for the profile picture (400x400)
    # instead of 'normal'
    if self.profile_image_url[t_user]:
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

    if self.profile_banner_url[t_user]:
        response = requests.get(self.profile_banner_url[t_user], stream=True)
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

    if self.profile_image_url:
        data.update({"avatar": self.avatar_path[t_user]})

    if self.profile_banner_url:
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
    if self.profile_image_url[t_user]:
        avatar = open(self.avatar_path[t_user], "rb")
        avatar_mime_type = guess_type(self.avatar_path[t_user])
        avatar_file_name = (
            f"pleromapyupload_{timestamp}_"
            f"{random_string(10)}"
            f"{mimetypes.guess_extension(avatar_mime_type)}"
        )
        files.update({"avatar": (avatar_file_name, avatar, avatar_mime_type)})
    if self.profile_banner_url[t_user]:
        header = open(self.header_path[t_user], "rb")
        header_mime_type = guess_type(self.header_path[t_user])
        header_file_name = (
            f"pleromapyupload_{timestamp}_"
            f"{random_string(10)}"
            f"{mimetypes.guess_extension(header_mime_type)}"
        )
        files.update({"header": (header_file_name, header, header_mime_type)})

    response = requests.patch(
        cred_url, data, headers=self.header_pleroma, files=files
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
