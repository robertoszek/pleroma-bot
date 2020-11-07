import pytest
import os

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


def test_user_invalid_visibility(mock_request):
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


def test_user_invalid_max_tweets(mock_request):
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


def test_check_pinned_tweet(sample_users, mock_request):
    test_user = TestUser()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            pinned = sample_user_obj.pinned_tweet_id
            assert pinned == test_user.pinned
            mock.get(f"{test_user.twitter_base_url_v2}/tweets/{pinned}"
                     f"?poll.fields=duration_minutes%2Cend_datetime%2Cid%2C"
                     f"options%2Cvoting_status&media.fields=duration_ms%2C"
                     f"height%2Cmedia_key%2Cpreview_image_url%2Ctype%2Curl%2C"
                     f"width%2Cpublic_metrics&expansions=attachments.poll_ids"
                     f"%2Cattachments.media_keys%2Cauthor_id%2C"
                     f"entities.mentions.username%2Cgeo.place_id%2C"
                     f"in_reply_to_user_id%2Creferenced_tweets.id%2C"
                     f"referenced_tweets.id.author_id&tweet.fields=attachments"
                     f"%2Cauthor_id%2Ccontext_annotations%2Cconversation_id%2"
                     f"Ccreated_at%2Centities%2Cgeo%2Cid%2Cin_reply_to_user_id"
                     f"%2Clang%2Cpublic_metrics%2Cpossibly_sensitive%2C"
                     f"referenced_tweets%2Csource%2Ctext%2Cwithheld",
                     json=mock_request['sample_data']['pinned_tweet'],
                     status_code=200)
            mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids={pinned}"
                     f"&expansions=attachments.poll_ids"
                     f"&poll.fields=duration_minutes%2Coptions",
                     json=mock_request['sample_data']['poll'],
                     status_code=200)
            pinned_file = os.path.join(
                os.getcwd(),
                'users',
                sample_user_obj.twitter_username,
                'pinned_id.txt'
            )
            with open(pinned_file, "w") as file:
                file.write(test_user.pinned + "\n")
            sample_user_obj.check_pinned()
            pinned_path = os.path.join(os.getcwd(),
                                       'users',
                                       sample_user_obj.twitter_username,
                                       'pinned_id.txt')
            with open(pinned_path, 'r', encoding='utf8') as pinned_file:
                assert pinned_file.readline().rstrip() == test_user.pinned
