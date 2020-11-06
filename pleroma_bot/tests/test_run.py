import pytest

from test_user import TestUser
from conftest import get_config_users
from pleroma_bot.cli import User
from pleroma_bot.cli import random_string


def test_random_string():
    """
    Check that random string returns a string of the desired length
    """
    random_10 = random_string(10)
    assert len(random_10) == 10


def test_user_replace_vars_in_str(sample_users):
    """
    Check that replace_vars_in_str replaces the var_name with the var_value
    correctly
    """
    test_user = TestUser()
    for sample_user in sample_users:
        user_obj = sample_user['user_obj']
        replace = user_obj.replace_vars_in_str(test_user.replace_str)
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
            sample_user_obj.get_date_last_pleroma_post()
            assert pinned == test_user.pinned
            assert pleroma_date == test_user.pleroma_date
            assert sample_user_obj.twitter_base_url == \
                   test_user.twitter_base_url
            assert sample_user_obj.twitter_token == test_user.twitter_token
            assert sample_user_obj.pleroma_token == test_user.pleroma_token
            assert sample_user_obj.twitter_base_url_v2 == \
                   test_user.twitter_base_url_v2
            assert sample_user_obj.nitter == test_user.nitter
            return mock


def test_user_invalid_visibility(rootdir, mock_request):
    """
    Check that an improper visibility value in the config raises a
    KeyError exception
    """
    test_user = TestUser()
    with pytest.raises(KeyError):
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_visibility.yml')
            for user_item in config_users['user_dict']:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/"
                         f"{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config_users['config']['pleroma_base_url']}"
                         f"/api/v1/accounts/"
                         f"{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config_users['config'])
                return user_obj


def test_user_invalid_max_tweets(rootdir, mock_request):
    """
    Check that an improper max_tweets value in the config raises a
    ValueError exception
    """
    test_user = TestUser()
    with pytest.raises(ValueError):
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_max_tweets_global.yml')
            for user_item in config_users['user_dict']:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/"
                         f"{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config_users['config']['pleroma_base_url']}"
                         f"/api/v1/accounts/"
                         f"{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config_users['config'])
    with pytest.raises(ValueError):
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_max_tweets_user.yml')
            for user_item in config_users['user_dict']:
                mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/"
                         f"{user_item['twitter_username']}",
                         json=mock_request['sample_data']['pinned'],
                         status_code=200)
                mock.get(f"{config_users['config']['pleroma_base_url']}"
                         f"/api/v1/accounts/"
                         f"{user_item['pleroma_username']}/statuses",
                         json=mock_request['sample_data']['pleroma_statuses'],
                         status_code=200)
                user_obj = User(user_item, config_users['config'])
                return user_obj


# def test_pinned_tweet():
#    pinned_id = '1315888762120011783'
