import os
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


def post_misskey(
        self,
        tweet: tuple,
        poll: dict,
        sensitive,
        media=None,
        cw: str = None
) -> str:
    """Post the given text to the Misskey instance associated with the
    User object

    :param media: List containing media
    :param tweet: Tuple containing tweet_id, tweet_text. The ID will be used to
    link to the Twitter status if 'signature' is True and to find related media
    tweet_text is the literal text to use when creating the post.
    :type tweet: tuple
    :param poll: dict of poll if attached to tweet
    :type poll: dict
    :param sensitive: if tweet is possibly sensitive or not
    :param cw: content warning to include
    :type cw: str
    :type sensitive: bool
    :returns: id of post
    :rtype: str
    """

    misskey_post_url = f"{self.pleroma_base_url}/api/notes/create"

    tweet_id, tweet_text, tweet_date, tweet_reply_id, retweet_id = tweet
    tweet_folder = os.path.join(self.tweets_temp_path, tweet_id)
    # config setting override tweet attr
    if self.sensitive:
        sensitive = self.sensitive
    media_ids = []
    posts = self.posts_ids[self.pleroma_base_url]

    if self.media_upload and retweet_id not in posts:
        if os.path.isdir(tweet_folder):
            media_files = sorted(os.listdir(tweet_folder))
            for file in media_files:
                file_path = os.path.join(tweet_folder, file)
                media_id = _upload_media_misskey(
                    self, file_path, sensitive, media
                )
                if media_id is not None:
                    media_ids.append(media_id)

    data = {
        "i": self.pleroma_token,
        "cw": cw,
    }
    if (
            tweet_id in posts
            and len(str(posts[tweet_id])) > 0
            and self.avoid_duplicates
    ):  # pragma: todo
        post_id = self.posts_ids[self.pleroma_base_url][tweet_id]

        misskey_posted_url = f"{self.pleroma_base_url}/api/notes/show"

        data_n = {
            "i": self.pleroma_token,
            "noteId": post_id,
        }
        response = requests.post(
            misskey_posted_url, json.dumps(data_n), headers=self.header_pleroma
        )
        if response.ok:
            logger.warning(
                _(
                    "Tweet already posted in Misskey:\t{} - {}."
                    " Skipping to avoid duplicates..."
                ).format(tweet_id, posts[tweet_id])
            )
            return post_id

    if (
            retweet_id
            and retweet_id in posts
            and len(str(posts[retweet_id])) > 0
    ):  # pragma: todo
        renote_id = posts[retweet_id]
        data.update({"renoteId": renote_id})
    else:
        data.update({"visibility": self.visibility, "text": tweet_text})

    if len(media_ids) != 0:
        data.update({"fileIds": media_ids})
    if (
            tweet_reply_id
            and tweet_reply_id in posts
            and len(posts[tweet_reply_id]) > 0
    ):  # pragma: todo
        post_reply_id = self.posts_ids[self.pleroma_base_url][tweet_reply_id]
        data.update({"replyId": post_reply_id})
    if poll and retweet_id not in posts:
        data.update(
            {
                "poll": {
                    "choices": poll["options"],
                    "multiple": False,
                    "expiredAfter": poll["expires_in"] * 1000
                }
            }
        )

    self.header_pleroma.update({"Content-Type": "text/plain;charset=UTF-8"})
    response = requests.post(
        misskey_post_url, json.dumps(data), headers=self.header_pleroma
    )
    if not response.ok:
        response.raise_for_status()
    logger.info(_("Post in Misskey:\t{}").format(str(response)))
    post_id = json.loads(response.text)["createdNote"]["id"]
    self.posts_ids[self.pleroma_base_url].update({tweet_id: post_id})
    return post_id


def get_date_last_misskey_post(self):
    """Gathers last post from the user in Pleroma and returns the date
    of creation.

    :returns: Date of last Misskey post in '%Y-%m-%dT%H:%M:%SZ' format
    """
    i_url = f"{self.pleroma_base_url}/api/i"
    data = {"i": self.pleroma_token}
    response = requests.post(
        i_url, json.dumps(data), headers=self.header_pleroma
    )
    i_id = response.json()["id"]
    notes_count = response.json()["notesCount"]

    if notes_count > 0:
        data = {
            "userId": i_id,
            "includeReplies": True,
            "limit": 1,
            "includeMyRenotes": True,
        }
        notes_url = f"{self.pleroma_base_url}/api/users/notes"
        response = requests.post(
            notes_url, json.dumps(data), headers=self.header_pleroma
        )

        notes = response.json()
        date_misskey = notes[0]["createdAt"]
    else:
        self.posts = "none_found"
        logger.warning(
            _("No posts were found in the target Fediverse account")
        )
        if self.first_time:
            date_misskey = self.force_date()
        else:
            date_misskey = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%dT%H:%M:%SZ"
            )
    return date_misskey


def _upload_media_misskey(self, file_path, sensitive=False, media=None):
    misskey_media_url = f"{self.pleroma_base_url}/api/drive/files/create"
    media_id = None
    media_file = open(file_path, "rb")
    file_size = os.stat(file_path).st_size
    size_mb = round(file_size / 1048576, 2)
    file = os.path.splitext(os.path.split(file_path)[1])[0]
    alt_text = None
    if media:
        key = file.split("-")[1].split(".")[0]
        m_item = media[key][0]
        alt_text = m_item["alt_text"] if "alt_text" in m_item else None
    mime_type = guess_type(os.path.join(file_path))
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

    data = {"i": self.pleroma_token}

    enc_mixin = requests.models.RequestEncodingMixin
    body, content_type = enc_mixin._encode_files(
        files, data
    )
    data = body
    headers = {
        "Cookie": f"igi={self.pleroma_token}",
        "Content-Type": content_type
    }
    response = requests.post(
        misskey_media_url,
        data=data,
        headers=headers
    )
    try:
        if not response.ok:
            response.raise_for_status()
        media_id = json.loads(response.text)["id"]
        if sensitive:
            update_url = f"{self.pleroma_base_url}/api/drive/files/update"
            data = {
                "fileId": media_id,
                "i": self.pleroma_token,
                "isSensitive": sensitive
            }
            response = requests.post(update_url, data=json.dumps(data))
            if not response.ok:
                response.raise_for_status()
        if alt_text:  # pragma
            update_url = f"{self.pleroma_base_url}/api/drive/files/update"
            data = {
                "fileId": media_id,
                "i": self.pleroma_token,
                "comment": alt_text
            }
            response = requests.post(update_url, data=json.dumps(data))
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
    return media_id


def update_misskey(self):
    """Update the Misskey user info with the one retrieved from Twitter
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

    data = {"i": self.pleroma_token}

    # Construct fields
    if len(self.fields) > 0:
        data.update({"fields": self.fields})
    data.update({
        "description": self.bio_text[t_user],
        "name": self.display_name[t_user]
    })

    if t_user in self.profile_image_url:
        data.update({"avatar": self.avatar_path[t_user]})

    if t_user in self.profile_banner_url:
        data.update({"header": self.header_path[t_user]})

    if len(self.fields) > 4:
        raise Exception(
            _(
                "Total number of metadata fields cannot exceed 4."
                "\nProvided: {}. Exiting..."
            ).format(len(self.fields))
        )

    id_avatar = None
    id_banner = None
    if t_user in self.profile_image_url:
        id_avatar = _upload_media_misskey(self, self.avatar_path[t_user])
    if t_user in self.profile_banner_url:
        id_banner = _upload_media_misskey(self, self.header_path[t_user])

    misskey_update_url = f"{self.pleroma_base_url}/api/i/update"

    if id_avatar:
        data.update({"avatarId": id_avatar})
    if id_banner:
        data.update({"bannerId": id_banner})
    response = requests.post(
        misskey_update_url, json.dumps(data)
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


def _misskey_update_bot_status(self, bot):
    i_update_url = f"{self.pleroma_base_url}/api/i/update"
    data = {"i": self.pleroma_token, "isBot": bot}
    response = requests.post(
        i_update_url, json.dumps(data), headers=self.header_pleroma
    )
    if not response.ok:  # pragma
        response.raise_for_status()


def _get_misskey_profile_info(self):
    i_url = f"{self.pleroma_base_url}/api/i"
    data = {"i": self.pleroma_token}
    response = requests.post(
        i_url, json.dumps(data), headers=self.header_pleroma
    )
    i_json = response.json()
    bot = i_json["isBot"]
    i_json["bot"] = bot
    return i_json
