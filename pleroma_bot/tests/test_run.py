import pytest
import logging

import os
import sys
import time
import string
import random
from json.decoder import JSONDecodeError

import re
import json
import yaml
import shutil
import requests
import requests_mock
import mimetypes

try:
    import magic
except ImportError:
    magic = None

from datetime import datetime, timedelta

from pleroma_bot.cli import *


def test_random_string():
    """
    Check that random string returns a string of the desired length
    """
    random_10 = random_string(10)
    assert len(random_10) == 10


def test_user(rootdir):
    """

    """
    sample_data_dir = os.path.join(rootdir, 'test_files', 'sample_data')
    sample_data = {}
    for file in os.listdir(sample_data_dir):
        data = os.path.join(sample_data_dir, file)
        with open(data, 'r', encoding='utf8') as f:
            sample_data[os.path.splitext(file)[0]] = json.load(f)

    twitter_base_url = 'http://api.twitter.com/1.1'
    twitter_base_url_v2 = 'https://api.twitter.com/2'
    with requests_mock.Mocker() as mock:
        mock.get(f"{twitter_base_url_v2}/tweets/search/recent", json=sample_data['tweets_v2'], status_code=200)
        mock.get(f"{twitter_base_url}/users/show.json", json=sample_data['twitter_info'], status_code=200)
        mock.get(f"{twitter_base_url}/statuses/show.json", json=sample_data['tweet'], status_code=200)
        mock.get(f"{twitter_base_url_v2}/tweets?ids=1323049466837032961&expansions=attachments.poll_ids&poll.fields"
                 f"=duration_minutes%2Coptions",
                 json=sample_data['poll'],
                 status_code=200)
        configs_dir = os.path.join(rootdir, 'test_files')
        for config in os.listdir(configs_dir):
            if os.path.isfile(os.path.join(configs_dir, config)):
                with open(os.path.join(configs_dir, config), 'r') as stream:
                    config = yaml.safe_load(stream)
                user_dict = config['users']
                for user_item in user_dict:
                    mock.get(f"{twitter_base_url_v2}/users/by/username/{user_item['twitter_username']}",
                             json=sample_data['pinned'],
                             status_code=200)
                    mock.get(f"{config['pleroma_base_url']}/api/v1/accounts/{user_item['pleroma_username']}/statuses",
                             json=sample_data['pleroma_statuses'],
                             status_code=200)
                    user = User(user_item, config)
                    assert user.twitter_base_url == "http://api.twitter.com/1.1"
