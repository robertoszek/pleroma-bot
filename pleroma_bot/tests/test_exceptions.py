import os

import pytest

import requests
from test_user import TestUser
from conftest import get_config_users
from pleroma_bot.cli import User


def test_user_invalid_pleroma_base(mock_request):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    test_user = TestUser()
    with pytest.raises(KeyError):
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_nopleroma.yml')
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


def test_user_missing_twitter_base(mock_request):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    test_user = TestUser()
    with mock_request['mock'] as mock:
        config_users = get_config_users('config_notwitter.yml')
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
            mock.get(f"{test_user.twitter_base_url}/users/"
                     f"show.json?screen_name={user_item['twitter_username']}",
                     json=mock_request['sample_data']['twitter_info'],
                     status_code=200)
            user_obj = User(user_item, config_users['config'])
            assert user_obj.twitter_base_url_v2 is not None
            assert user_obj.twitter_base_url is not None
            assert user_obj.twitter_base_url == test_user.twitter_base_url
            assert (
                user_obj.twitter_base_url_v2 ==
                test_user.twitter_base_url_v2
            )
        return user_obj


def test_user_nitter_global(mock_request):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    test_user = TestUser()
    with mock_request['mock'] as mock:
        config_users = get_config_users('config_nitter_global.yml')
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
            mock.get(f"{test_user.twitter_base_url}/users/"
                     f"show.json?screen_name={user_item['twitter_username']}",
                     json=mock_request['sample_data']['twitter_info'],
                     status_code=200)
            user_obj = User(user_item, config_users['config'])
            nitter_url = f"http://nitter.net/{user_obj.twitter_username}"
            assert user_obj.twitter_url is not None
            assert user_obj.twitter_url == nitter_url
        config_users = get_config_users('config_nonitter.yml')
        # No global
        for user_item in config_users['user_dict']:
            user_obj = User(user_item, config_users['config'])
            twitter_url = f"http://twitter.com/{user_obj.twitter_username}"
            assert user_obj.twitter_url == twitter_url
        return user_obj


def test_user_invalid_visibility(mock_request):
    """
    Check that an improper visibility value in the config raises a
    KeyError exception
    """
    with pytest.raises(KeyError) as error_info:
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_visibility.yml')
            for user_item in config_users['user_dict']:
                user_obj = User(user_item, config_users['config'])
                user_obj['mock'] = mock
    str_error = (
        "'Visibility not supported! Values allowed are: "
        "public, unlisted, private and direct'"
    )
    assert str(error_info.value) == str(str_error)


def test_user_invalid_max_tweets(mock_request):
    """
    Check that an improper max_tweets value in the config raises a
    ValueError exception
    """
    error_str = 'max_tweets must be between 10 and 100. max_tweets: 5'
    with pytest.raises(ValueError) as error_info:
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_max_tweets_global.yml')
            for user_item in config_users['user_dict']:
                user_obj = User(user_item, config_users['config'])
    assert str(error_info.value) == error_str
    with pytest.raises(ValueError):
        with mock_request['mock'] as mock:
            config_users = get_config_users('config_max_tweets_user.yml')
            for user_item in config_users['user_dict']:
                user_obj = User(user_item, config_users['config'])
            user_obj['mock'] = mock
    assert str(error_info.value) == error_str


def test_check_pinned_exception_user(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = TestUser()
        url_user = (
            f"{test_user.twitter_base_url_v2}/tweets/{test_user.pinned}"
            f"?poll.fields=duration_minutes%2Cend_datetime%2Cid"
            f"%2Coptions%2Cvoting_status&media.fields=duration_ms"
            f"%2Cheight%2Cmedia_key%2Cpreview_image_url%2Ctype"
            f"%2Curl%2Cwidth%2Cpublic_metrics&expansions="
            f"attachments.poll_ids%2Cattachments.media_keys"
            f"%2Cauthor_id%2Centities.mentions.username"
            f"%2Cgeo.place_id%2Cin_reply_to_user_id%2C"
            f"referenced_tweets.id%2Creferenced_tweets.id."
            f"author_id&tweet.fields=attachments%2Cauthor_id"
            f"%2Ccontext_annotations%2Cconversation_id%2C"
            f"created_at%2Centities%2Cgeo%2Cid%2C"
            f"in_reply_to_user_id%2Clang%2Cpublic_metrics%2C"
            f"possibly_sensitive%2Creferenced_tweets%2Csource%2C"
            f"text%2Cwithheld"
        )
        # Test exceptions
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                pinned = sample_user_obj.pinned_tweet_id
                mock.get(url_user,
                         json=mock_request['sample_data']['pinned_tweet'],
                         status_code=500)
                mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids={pinned}"
                         f"&expansions=attachments.poll_ids"
                         f"&poll.fields=duration_minutes%2Coptions",
                         json=mock_request['sample_data']['poll'],
                         status_code=200)
                sample_user_obj.check_pinned()

    exception_value = (
        f"500 Server Error: None for url: {url_user}"
    )
    assert str(error_info.value) == exception_value
    pin_p = os.path.join(sample_user_obj.user_path, "pinned_id_pleroma.txt")
    pin_t = os.path.join(sample_user_obj.user_path, "pinned_id.txt")
    if os.path.isfile(pin_p):
        os.remove(pin_p)
    if os.path.isfile(pin_t):
        os.remove(pin_t)


def test_check_pinned_exception_tweet(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = TestUser()
        url_tweet = (
            f"{test_user.twitter_base_url_v2}/tweets?ids={test_user.pinned}"
            f"&expansions=attachments.poll_ids"
            f"&poll.fields=duration_minutes%2Coptions"
        )
        # Test exception
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                pinned = sample_user_obj.pinned_tweet_id
                mock.get(f"{test_user.twitter_base_url_v2}/tweets/{pinned}"
                         f"?poll.fields=duration_minutes%2Cend_datetime%2Cid"
                         f"%2Coptions%2Cvoting_status&media.fields=duration_ms"
                         f"%2Cheight%2Cmedia_key%2Cpreview_image_url%2Ctype"
                         f"%2Curl%2Cwidth%2Cpublic_metrics&expansions="
                         f"attachments.poll_ids%2Cattachments.media_keys"
                         f"%2Cauthor_id%2Centities.mentions.username"
                         f"%2Cgeo.place_id%2Cin_reply_to_user_id%2C"
                         f"referenced_tweets.id%2Creferenced_tweets.id."
                         f"author_id&tweet.fields=attachments%2Cauthor_id"
                         f"%2Ccontext_annotations%2Cconversation_id%2C"
                         f"created_at%2Centities%2Cgeo%2Cid%2C"
                         f"in_reply_to_user_id%2Clang%2Cpublic_metrics%2C"
                         f"possibly_sensitive%2Creferenced_tweets%2Csource%2C"
                         f"text%2Cwithheld",
                         json=mock_request['sample_data']['pinned_tweet'],
                         status_code=200)
                mock.get(url_tweet,
                         json=mock_request['sample_data']['poll'],
                         status_code=500)

                sample_user_obj.check_pinned()

    exception_value = (
        f"500 Server Error: None for url: {url_tweet}"
    )
    assert str(error_info.value) == exception_value
    pin_p = os.path.join(sample_user_obj.user_path, "pinned_id_pleroma.txt")
    pin_t = os.path.join(sample_user_obj.user_path, "pinned_id.txt")
    if os.path.isfile(pin_p):
        os.remove(pin_p)
    if os.path.isfile(pin_t):
        os.remove(pin_t)


def test_pin_pleroma_exception(sample_users, mock_request):
    test_user = TestUser()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            mock.post(f"{test_user.pleroma_base_url}"
                      f"/api/v1/statuses/{test_user.pleroma_pinned_new}/pin",
                      json={},
                      status_code=500)
            pin_id = sample_user_obj.pin_pleroma(test_user.pleroma_pinned_new)
            assert pin_id is None
    pin_p = os.path.join(sample_user_obj.user_path, "pinned_id_pleroma.txt")
    os.remove(pin_p)


def test_unpin_pleroma_exception(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = TestUser()
        url_unpin = (
            f"{test_user.pleroma_base_url}"
            f"/api/v1/statuses/"
            f"{test_user.pleroma_pinned}/unpin"
        )
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                mock.post(url_unpin,
                          json={},
                          status_code=500)
                pinned_file = os.path.join(
                    sample_user_obj.user_path, "pinned_id_pleroma.txt"
                )
                with open(pinned_file, 'w') as file:
                    file.write(test_user.pleroma_pinned)
                file.close()
                sample_user_obj.unpin_pleroma(pinned_file)

    exception_value = (
        f"500 Server Error: None for url: {url_unpin}"
    )
    assert str(error_info.value) == exception_value
    os.remove(pinned_file)
