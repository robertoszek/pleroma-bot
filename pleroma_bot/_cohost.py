import base64
import requests
from hashlib import pbkdf2_hmac
from datetime import datetime, timedelta

from . import logger
from .i18n import _


def _login_cohost(self):
    email = self.pleroma_username
    passwd = self.pleroma_token
    cohost_salt_url = f"{self.pleroma_base_url}/api/v1/login/salt"
    data = {"email": email}

    response = requests.get(
        cohost_salt_url, data
    )
    salt = response.json()['salt']
    chars = ['-', '_']
    salt = ''.join('A' if ch in chars else ch for ch in salt)
    salt = salt + "=="

    salt = base64.b64decode(salt.encode("ascii"))

    hash = pbkdf2_hmac("sha384", passwd.encode("utf-8"), salt, 200000, 128)
    client_hash = base64.b64encode(hash).decode("ascii")

    data.update({"clientHash": client_hash})

    cohost_login_url = f"{self.pleroma_base_url}/api/v1/login"
    response = requests.post(cohost_login_url, data)
    cookie = response.headers['set-cookie'].split(";")[0].split("=")[1]
    self.cohost_cookies = {'connect.sid': cookie}

    return cookie


def _get_cohost_profile_info(self):
    self._login_cohost()
    cohost_info_url = f"{self.pleroma_base_url}/api/v1//trpc/login.loggedIn"
    response = requests.get(cohost_info_url, cookies=self.cohost_cookies)
    user_info = response.json()['result']['data']
    self.cohost_user_id = user_info["userId"]
    self.cohost_project_id = user_info["projectId"]
    self.cohost_project_handle = user_info["projectHandle"]


def get_date_last_cohost_post(self):
    handle = self.cohost_project_handle
    page = 0
    cohost_posts_url = (
        f"{self.pleroma_base_url}/api/v1/project/{handle}/posts?page={page}"
    )
    response = requests.get(cohost_posts_url, cookies=self.cohost_cookies)
    posts_json = response.json()['items']
    if len(posts_json) > 0:
        last_date = posts_json[0]["publishedAt"]
    else:
        self.posts = "none_found"
        logger.warning(
            _("No posts were found in the target Fediverse account")
        )
        if self.first_time:
            last_date = self.force_date()
        else:
            last_date = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%dT%H:%M:%SZ"
            )

    return last_date
