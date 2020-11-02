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
from test_user import TestUser

def test_random_string():
    """
    Check that random string returns a string of the desired length
    """
    random_10 = random_string(10)
    assert len(random_10) == 10


def test_user_replace_vars_in_str(sample_users):
    """
    Check that replace_vars_in_str replaces the var_name with the var_value correctly
    """
    test_user = TestUser()
    for sample_user in sample_users:
        replace = sample_user['user_obj'].replace_vars_in_str(test_user.replace_str)
        assert replace == sample_user['user_obj'].twitter_url


def test_user_attrs(sample_users):
    """
    Check that test user matches sample data fed by the mock
    """
    test_user = TestUser()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            pleroma_date = sample_user_obj.get_date_last_pleroma_post()
            pinned = sample_user_obj.pinned_tweet_id
            assert pinned == test_user.pinned
            assert pleroma_date == test_user.pleroma_date
            assert sample_user_obj.twitter_base_url == test_user.twitter_base_url
            assert sample_user_obj.twitter_token == test_user.twitter_token
            assert sample_user_obj.pleroma_token == test_user.pleroma_token
            assert sample_user_obj.twitter_base_url_v2 == test_user.twitter_base_url_v2
            assert sample_user_obj.nitter == test_user.nitter


def test_user_invalid_visibility(rootdir, mock_request):
    test_user = TestUser()
    with pytest.raises(KeyError):
        with mock_request['mock'] as mock:
            configs_dir = os.path.join(rootdir, 'test_files')
            with open(os.path.join(configs_dir, 'config_visibility.yml'), 'r',  encoding='utf8') as stream:
                config = yaml.safe_load(stream)
            user_dict = config['users']
            for user_item in user_dict:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config['pleroma_base_url']}/api/v1/accounts/{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config)


def test_user_invalid_max_tweets(rootdir, mock_request):
    test_user = TestUser()
    with pytest.raises(ValueError):
        with mock_request['mock'] as mock:
            configs_dir = os.path.join(rootdir, 'test_files')
            with open(os.path.join(configs_dir, 'config_max_tweets_global.yml'), 'r',  encoding='utf8') as stream:
                config = yaml.safe_load(stream)
            user_dict = config['users']
            for user_item in user_dict:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config['pleroma_base_url']}/api/v1/accounts/{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config)
    with pytest.raises(ValueError):
        with mock_request['mock'] as mock:
            configs_dir = os.path.join(rootdir, 'test_files')
            with open(os.path.join(configs_dir, 'config_max_tweets_user.yml'), 'r',  encoding='utf8') as stream:
                config = yaml.safe_load(stream)
            user_dict = config['users']
            for user_item in user_dict:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config['pleroma_base_url']}/api/v1/accounts/{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config)
