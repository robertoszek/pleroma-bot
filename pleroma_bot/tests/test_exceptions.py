import os
import re
import sys
import time

import pytest
import shutil
import requests
import logging
import urllib.parse
from unittest.mock import patch

from test_user import UserTemplate
from conftest import get_config_users

from pleroma_bot import cli
from pleroma_bot.cli import User
from pleroma_bot._utils import Locker
from pleroma_bot._error import TimeoutLocker


def test_user_invalid_pleroma_base(mock_request):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    with mock_request['mock'] as mock:
        config_users = get_config_users('config_nopleroma.yml')
        for user_item in config_users['user_dict']:
            with pytest.raises(KeyError) as error_info:
                User(user_item, config_users['config'], os.getcwd())
            exception_value = (
                "'No Pleroma URL defined in config! [pleroma_base_url]'"
            )
            assert str(error_info.value) == exception_value
    return mock


def test_user_missing_twitter_base(sample_users):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            config_users = get_config_users('config_notwitter.yml')
            for user_item in config_users['user_dict']:
                user_obj = User(user_item, config_users['config'], os.getcwd())
                assert user_obj.twitter_base_url_v2 is not None
                assert user_obj.twitter_base_url is not None
                assert user_obj.twitter_base_url == test_user.twitter_base_url
                assert (
                    user_obj.twitter_base_url_v2 ==
                    test_user.twitter_base_url_v2
                )
        return mock


def test_user_nitter_global(sample_users):
    """
    Check that a missing pleroma_base_url raises a KeyError exception
    """
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            config_users = get_config_users('config_nitter_global.yml')
            for user_item in config_users['user_dict']:
                t_users = user_item["twitter_username"]
                t_users_list = isinstance(t_users, list)
                t_users = t_users if t_users_list else [t_users]
                for t_user in t_users:
                    user_obj = User(
                        user_item,
                        config_users['config'],
                        os.getcwd()
                    )
                    idx = user_obj.twitter_username.index(t_user)
                    nitter_url = f"https://nitter.net/" \
                                 f"{user_obj.twitter_username[idx]}"
                    assert user_obj.twitter_url[t_user] is not None
                    assert user_obj.twitter_url[t_user] == nitter_url
            config_users = get_config_users('config_nonitter.yml')
            # No global
            for user_item in config_users['user_dict']:
                t_users = user_item["twitter_username"]
                t_users_list = isinstance(t_users, list)
                t_users = t_users if t_users_list else [t_users]
                for t_user in t_users:
                    user_obj = User(
                        user_item,
                        config_users['config'],
                        os.getcwd()
                    )
                    twitter_url = f"http://twitter.com/" \
                                  f"{user_obj.twitter_username[idx]}"
                    assert user_obj.twitter_url[t_user] == twitter_url
        return mock


def test_user_invalid_visibility(sample_users):
    """
    Check that an improper visibility value in the config raises a
    KeyError exception
    """
    with pytest.raises(KeyError) as error_info:
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                config_users = get_config_users('config_visibility.yml')
                for user_item in config_users['user_dict']:
                    user_obj = User(
                        user_item, config_users['config'], os.getcwd()
                    )
                    user_obj['mock'] = mock
    str_error = (
        "'Visibility not supported! Values allowed are: "
        "public, unlisted, private, direct'"
    )
    assert str(error_info.value) == str(str_error)


def test_user_invalid_max_tweets(sample_users):
    """
    Check that an improper max_tweets value in the config raises a
    ValueError exception
    """
    error_str = 'max_tweets must be between 10 and 3200. max_tweets: 5'
    with pytest.raises(ValueError) as error_info:
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                config_users = get_config_users('config_max_tweets_global.yml')
                for user_item in config_users['user_dict']:
                    user_obj = User(
                        user_item, config_users['config'], os.getcwd()
                    )
                    start_time = user_obj.get_date_last_pleroma_post()
                    user_obj.get_tweets(start_time=start_time)

    assert str(error_info.value) == error_str
    with pytest.raises(ValueError):
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                config_users = get_config_users('config_max_tweets_user.yml')
                for user_item in config_users['user_dict']:
                    user_obj = User(
                        user_item, config_users['config'], os.getcwd()
                    )
                    start_time = user_obj.get_date_last_pleroma_post()
                    user_obj.get_tweets(start_time=start_time)
                user_obj['mock'] = mock
    assert str(error_info.value) == error_str
    return mock


def test_check_pinned_exception_user(sample_users, mock_request):
    test_user = UserTemplate()
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
            HTTPError = requests.exceptions.HTTPError
            t_users = sample_user_obj.twitter_username
            t_users_list = isinstance(t_users, list)
            t_users = t_users if t_users_list else [t_users]

            mock.get(url_user,
                     json=mock_request['sample_data']['pinned_tweet'],
                     status_code=500)
            mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids={pinned}"
                     f"&expansions=attachments.poll_ids"
                     f"&poll.fields=duration_minutes%2Coptions",
                     json=mock_request['sample_data']['poll'],
                     status_code=200)

            for t_user in t_users:
                with pytest.raises(HTTPError) as error_info:
                    sample_user_obj.check_pinned()
                exception_value = (
                    f"500 Server Error: None for url: {url_user}"
                )
                assert str(error_info.value) == exception_value
                pin_p = os.path.join(
                    sample_user_obj.user_path[t_user], "pinned_id_pleroma.txt"
                )
                pin_t = os.path.join(
                    sample_user_obj.user_path[t_user], "pinned_id.txt"
                )
                if os.path.isfile(pin_p):
                    os.remove(pin_p)
                if os.path.isfile(pin_t):
                    os.remove(pin_t)


def test_check_pinned_exception_tweet(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = UserTemplate()
        url_tweet = (
            f"{test_user.twitter_base_url_v2}/tweets?ids={test_user.pinned}"
            f"&expansions=attachments.poll_ids"
            f"&poll.fields=duration_minutes%2Coptions"
        )
        # Test exception
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                mock.get(url_tweet,
                         json=mock_request['sample_data']['poll'],
                         status_code=500)
                sample_user_obj.check_pinned()

    exception_value = (
        f"500 Server Error: None for url: {url_tweet}"
    )
    assert str(error_info.value) == exception_value
    for t_user in sample_user_obj.twitter_username:
        pin_p = os.path.join(
            sample_user_obj.user_path[t_user],
            "pinned_id_pleroma.txt"
        )
        pin_t = os.path.join(
            sample_user_obj.user_path[t_user],
            "pinned_id.txt"
        )
        if os.path.isfile(pin_p):
            os.remove(pin_p)
        if os.path.isfile(pin_t):
            os.remove(pin_t)


def test_pin_pleroma_exception(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            mock.post(f"{test_user.pleroma_base_url}"
                      f"/api/v1/statuses/{test_user.pleroma_pinned_new}/pin",
                      json={},
                      status_code=500)
            pin_id = sample_user_obj.pin_pleroma(test_user.pleroma_pinned_new)
            assert pin_id is None
            for t_user in sample_user_obj.twitter_username:
                pin_p = os.path.join(
                    sample_user_obj.user_path[t_user],
                    "pinned_id_pleroma.txt"
                )
                os.remove(pin_p)


def test_pin_misskey_exception(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            mock.post(f"{test_user.pleroma_base_url}"
                      f"/api/i/pin",
                      json={},
                      status_code=500)
            pin_id = sample_user_obj.pin_misskey(test_user.pleroma_pinned_new)
            assert pin_id is None
            for t_user in sample_user_obj.twitter_username:
                pin_p = os.path.join(
                    sample_user_obj.user_path[t_user],
                    "pinned_id_pleroma.txt"
                )
                os.remove(pin_p)


def test_unpin_pleroma_exception(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = UserTemplate()
        url_unpin = (
            f"{test_user.pleroma_base_url}"
            f"/api/v1/statuses/"
            f"{test_user.pleroma_pinned}/unpin"
        )
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                for t_user in sample_user_obj.twitter_username:
                    mock.post(url_unpin,
                              json={},
                              status_code=500)
                    pinned_file = os.path.join(
                        sample_user_obj.user_path[t_user],
                        "pinned_id_pleroma.txt"
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


def test_unpin_misskey_exception(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = UserTemplate()
        url_unpin = (
            f"{test_user.pleroma_base_url}"
            f"/api/i/unpin"
        )
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                for t_user in sample_user_obj.twitter_username:
                    mock.post(url_unpin,
                              json={},
                              status_code=500)
                    pinned_file = os.path.join(
                        sample_user_obj.user_path[t_user],
                        "pinned_id_pleroma.txt"
                    )
                    with open(pinned_file, 'w') as file:
                        file.write(test_user.pleroma_pinned)
                    file.close()
                    sample_user_obj.unpin_misskey(pinned_file)

    exception_value = (
        f"500 Server Error: None for url: {url_unpin}"
    )
    assert str(error_info.value) == exception_value
    os.remove(pinned_file)


def test_get_date_last_pleroma_post_exception(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = UserTemplate()

        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                url_statuses = (
                    f"{test_user.pleroma_base_url}"
                    f"/api/v1/accounts/"
                    f"{sample_user_obj.pleroma_username}/statuses"
                )
                mock.get(
                    url_statuses,
                    json=mock_request['sample_data']['pleroma_statuses_pin'],
                    status_code=500
                )
                sample_user_obj.get_date_last_pleroma_post()

    exception_value = f"500 Server Error: None for url: {url_statuses}"
    assert str(error_info.value) == exception_value


def test_get_tweets_unknown_version(sample_users, mock_request):
    with pytest.raises(ValueError) as error_info:
        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                sample_user_obj._get_tweets("nonsense")
    assert str(error_info.value) == 'API version not supported: nonsense'
    return mock


def test_unpin_pleroma_statuses_exception(sample_users, mock_request):
    with pytest.raises(requests.exceptions.HTTPError) as error_info:
        test_user = UserTemplate()

        for sample_user in sample_users:
            with sample_user['mock'] as mock:
                sample_user_obj = sample_user['user_obj']
                for t_user in sample_user_obj.twitter_username:
                    url_statuses = (
                        f"{test_user.pleroma_base_url}"
                        f"/api/v1/accounts/"
                        f"{sample_user_obj.pleroma_username}/statuses"
                    )
                    sample_data = mock_request['sample_data']
                    mock.get(
                        url_statuses,
                        json=sample_data['pleroma_statuses_pin'],
                        status_code=500
                    )
                    pinned_file = os.path.join(
                        sample_user_obj.user_path[t_user],
                        "pinned_id_pleroma.txt"
                    )
                    sample_user_obj.unpin_pleroma(pinned_file)

    exception_value = f"500 Server Error: None for url: {url_statuses}"
    assert str(error_info.value) == exception_value


def test__get_pinned_tweet_id_exception(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                pinned = sample_user_obj.pinned_tweet_id
                assert pinned == test_user.pinned
                pinned_url = (
                    f"{test_user.twitter_base_url_v2}/users/by/username/"
                    f"{t_user}?user.fields="
                    f"pinned_tweet_id&expansions=pinned_tweet_id&"
                    f"tweet.fields=entities"
                )
                mock.get(pinned_url,
                         json=mock_request['sample_data']['pinned'],
                         status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_pinned_tweet_id()
                exception_value = f"500 Server Error: " \
                                  f"None for url: {pinned_url}"
                assert str(error_info.value) == exception_value


def test_post_pleroma_exception(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                tweets_folder = sample_user_obj.tweets_temp_path
                tweet_folder = os.path.join(tweets_folder, test_user.pinned)
                os.makedirs(tweet_folder, exist_ok=True)
                post_url = f"{test_user.pleroma_base_url}/api/v1/statuses"
                mock.post(post_url, status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.post_pleroma(
                        (test_user.pinned, "Test", ""), None, False
                    )
                exception_value = f"500 Server Error: None for url: {post_url}"
                assert str(error_info.value) == exception_value
                os.rmdir(tweet_folder)


def test_post_misskey_exception(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                tweets_folder = sample_user_obj.tweets_temp_path
                tweet_folder = os.path.join(tweets_folder, test_user.pinned)
                os.makedirs(tweet_folder, exist_ok=True)
                post_url = f"{test_user.pleroma_base_url}/api/notes/create"
                mock.post(post_url, status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.post_misskey(
                        (test_user.pinned, "Test", ""), None, False
                    )
                exception_value = f"500 Server Error: None for url: {post_url}"
                assert str(error_info.value) == exception_value
                os.rmdir(tweet_folder)


def test_update_pleroma_exception(rootdir, mock_request, sample_users, caplog):
    test_user = UserTemplate()
    twitter_info = mock_request['sample_data']['twitter_info']
    banner_url = f"{twitter_info['profile_banner_url']}/1500x500"
    profile_small_url = twitter_info['profile_image_url_https']
    profile_url = re.sub(r"normal", "400x400", profile_small_url)

    test_files_dir = os.path.join(rootdir, 'test_files')
    sample_data_dir = os.path.join(test_files_dir, 'sample_data')
    media_dir = os.path.join(sample_data_dir, 'media')
    banner = os.path.join(media_dir, 'banner.jpg')

    profile_banner = open(banner, 'rb')
    profile_banner_content = profile_banner.read()
    profile_banner.close()

    profile_pic = os.path.join(media_dir, 'default_profile_normal.png')
    profile_image = open(profile_pic, 'rb')
    profile_image_content = profile_image.read()
    profile_image.close()

    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_pleroma()
                exception_value = f"500 Server Error: None " \
                                  f"for url: {profile_url}"
                assert str(error_info.value) == exception_value
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=500)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_pleroma()
                exception_value = f"500 Server Error: " \
                                  f"None for url: {banner_url}"
                assert str(error_info.value) == exception_value
                cred_url = (
                    f"{test_user.pleroma_base_url}/api/v1/"
                    f"accounts/update_credentials"
                )
                mock.patch(cred_url,
                           status_code=500)
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=200)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_pleroma()
                exception_value = f"500 Server Error: None for url: {cred_url}"
                assert str(error_info.value) == exception_value
                mock.patch(cred_url,
                           status_code=422)
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=200)
                with caplog.at_level(logging.ERROR):
                    sample_user_obj.update_pleroma()
                    exception_value = (
                        "Exception occurred"
                        "\nError code 422"
                        "\n(Unprocessable Entity)"
                        "\nPlease check that the bio text or "
                        "the metadata fields text"
                        "\naren't too long."
                    )
                    assert exception_value in caplog.text
                mock_fields = [
                    {'name': 'Field1', 'value': 'Value1'},
                    {'name': 'Field2', 'value': 'Value2'},
                    {'name': 'Field3', 'value': 'Value3'},
                    {'name': 'Field4', 'value': 'Value4'},
                    {'name': 'Field5', 'value': 'Value5'}
                ]
                sample_user_obj.fields = mock_fields
                with pytest.raises(Exception) as error_info:
                    sample_user_obj.update_pleroma()
                exception_value = (
                    f"Total number of metadata fields cannot "
                    f"exceed 4.\nProvided: {len(mock_fields)}. Exiting..."
                )
                assert str(error_info.value) == exception_value


def test_update_misskey_exception(rootdir, mock_request, sample_users, caplog):
    test_user = UserTemplate()
    twitter_info = mock_request['sample_data']['twitter_info']
    banner_url = f"{twitter_info['profile_banner_url']}/1500x500"
    profile_small_url = twitter_info['profile_image_url_https']
    profile_url = re.sub(r"normal", "400x400", profile_small_url)

    test_files_dir = os.path.join(rootdir, 'test_files')
    sample_data_dir = os.path.join(test_files_dir, 'sample_data')
    media_dir = os.path.join(sample_data_dir, 'media')
    banner = os.path.join(media_dir, 'banner.jpg')

    profile_banner = open(banner, 'rb')
    profile_banner_content = profile_banner.read()
    profile_banner.close()

    profile_pic = os.path.join(media_dir, 'default_profile_normal.png')
    profile_image = open(profile_pic, 'rb')
    profile_image_content = profile_image.read()
    profile_image.close()

    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            sample_user_obj.instance = "misskey"
            for t_user in sample_user_obj.twitter_username:
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_misskey()
                exception_value = f"500 Server Error: None " \
                                  f"for url: {profile_url}"
                assert str(error_info.value) == exception_value
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=500)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_misskey()
                exception_value = f"500 Server Error: " \
                                  f"None for url: {banner_url}"
                assert str(error_info.value) == exception_value
                cred_url = (
                    f"{test_user.pleroma_base_url}/api/i/update"
                )
                mock.post(cred_url,
                          status_code=500)
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=200)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj.update_misskey()
                exception_value = f"500 Server Error: None for url: {cred_url}"
                assert str(error_info.value) == exception_value
                mock.post(cred_url,
                          status_code=422)
                mock.get(profile_url,
                         content=profile_image_content,
                         status_code=200)
                mock.get(banner_url,
                         content=profile_banner_content,
                         status_code=200)
                with caplog.at_level(logging.ERROR):
                    sample_user_obj.update_misskey()
                    exception_value = (
                        "Exception occurred"
                        "\nError code 422"
                        "\n(Unprocessable Entity)"
                        "\nPlease check that the bio text or "
                        "the metadata fields text"
                        "\naren't too long."
                    )
                    assert exception_value in caplog.text
                mock_fields = [
                    {'name': 'Field1', 'value': 'Value1'},
                    {'name': 'Field2', 'value': 'Value2'},
                    {'name': 'Field3', 'value': 'Value3'},
                    {'name': 'Field4', 'value': 'Value4'},
                    {'name': 'Field5', 'value': 'Value5'}
                ]
                sample_user_obj.fields = mock_fields
                with pytest.raises(Exception) as error_info:
                    sample_user_obj.update_misskey()
                exception_value = (
                    f"Total number of metadata fields cannot "
                    f"exceed 4.\nProvided: {len(mock_fields)}. Exiting..."
                )
                assert str(error_info.value) == exception_value


def test_post_misskey_update_exception(rootdir, caplog, global_mock):
    test_user = UserTemplate()
    config_users = get_config_users('config_mk.yml')
    for user_item in config_users['user_dict']:
        test_files_dir = os.path.join(rootdir, 'test_files')
        sample_data_dir = os.path.join(
            test_files_dir, 'sample_data'
        )
        media_dir = os.path.join(sample_data_dir, 'media')
        png = os.path.join(media_dir, 'image.png')
        svg = os.path.join(media_dir, 'image.svg')
        mp4 = os.path.join(media_dir, 'video.mp4')
        gif = os.path.join(media_dir, "animated_gif.gif")

        media_update_url = (
            f"{test_user.pleroma_base_url}/api/drive/files/update"
        )
        with global_mock as mock:
            user_obj = User(user_item, config_users['config'], os.getcwd())
            user_obj.instance = "misskey"

            tweet_folder = os.path.join(
                user_obj.tweets_temp_path, test_user.pinned
            )
            os.makedirs(tweet_folder, exist_ok=True)
            shutil.copy(png, tweet_folder)
            shutil.copy(svg, tweet_folder)
            shutil.copy(mp4, tweet_folder)
            shutil.copy(gif, tweet_folder)

            err_ex = requests.exceptions.HTTPError
            mock.post(mock.post(media_update_url, status_code=500))
            if user_obj.sensitive and user_obj.media_upload:
                with pytest.raises(err_ex) as error_info:
                    user_obj.post((test_user.pinned, "", ""), None, False)
                exception_value = (
                    f"500 Server Error: None for url: {media_update_url}"
                )
                assert str(error_info.value) == exception_value


def test__get_tweets_exception(sample_users, mock_request):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']

            for t_user in sample_user_obj.twitter_username:
                idx = sample_user_obj.twitter_username.index(t_user)
                tweet_id_url = (
                    f"{sample_user_obj.twitter_base_url}"
                    f"/statuses/show.json?id="
                    f"{str(sample_user_obj.pinned_tweet_id)}"
                )

                mock.get(tweet_id_url, status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_tweets(
                        "v1.1", sample_user_obj.pinned_tweet_id
                    )
                exception_value = f"500 Server Error: " \
                                  f"None for url: {tweet_id_url}"
                assert str(error_info.value) == exception_value
                tweets_url = (
                    f"{sample_user_obj.twitter_base_url}"
                    f"/statuses/user_timeline.json?screen_name="
                    f"{sample_user_obj.twitter_username[idx]}"
                    f"&count={str(sample_user_obj.max_tweets)}"
                    f"&include_rts=true"
                )
                mock.get(tweets_url, status_code=500)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_tweets("v1.1")
                exception_value = f"500 Server Error: " \
                                  f"None for url: {tweets_url}"
                assert str(error_info.value) == exception_value


def test__get_tweets_v2_exception(sample_users):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                idx = sample_user_obj.twitter_username.index(t_user)
                date = sample_user_obj.get_date_last_pleroma_post()
                date_encoded = urllib.parse.quote(date)
                tweets_url = (
                    f"{test_user.twitter_base_url_v2}/users/2244994945/tweets"
                    f"?max_results={sample_user_obj.max_tweets}&start_time"
                    f"={date_encoded}&poll."
                    f"fields=duration_minutes%2Cend_datetime%2Cid"
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
                count = sample_user_obj.max_tweets + 100
                start_time = sample_user_obj.get_date_last_pleroma_post()
                sample_user_obj._get_tweets_v2(
                    start_time=start_time, t_user=t_user, count=count
                )
                mock.get(tweets_url, status_code=500)

                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_tweets(
                        "v2", start_time=start_time, t_user=t_user
                    )

                exception_value = f"500 Server Error: " \
                                  f"None for url: {tweets_url}"
                assert str(error_info.value) == exception_value

                tweets_url = (
                    f"{test_user.twitter_base_url_v2}/users/by?"
                    f"usernames={sample_user_obj.twitter_username[idx]}"
                )
                mock.get(tweets_url, status_code=500)
                start_time = sample_user_obj.get_date_last_pleroma_post()
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_tweets(
                        "v2", start_time=start_time, t_user=t_user
                    )
                exception_value = f"500 Server Error: " \
                                  f"None for url: {tweets_url}"
                assert str(error_info.value) == exception_value


def test__get_twitter_info_exception(sample_users):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            t_users = sample_user_obj.twitter_username
            t_users_list = isinstance(t_users, list)
            t_users = t_users if t_users_list else [t_users]
            for t_user in t_users:
                idx = sample_user_obj.twitter_username.index(t_user)
                info_url = (
                    f"{sample_user_obj.twitter_base_url}"
                    f"/users/show.json?screen_name="
                    f"{sample_user_obj.twitter_username[idx]}"
                )
                mock.get(info_url, status_code=500)
                err_ex = requests.exceptions.HTTPError
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_twitter_info()
                exception_value = f"500 Server Error: None for url: {info_url}"
                assert str(error_info.value) == exception_value

                url_username = (
                    f"https://api.twitter.com/2/users/by/username/"
                    f"{t_user}?user.fields=created_at%2Cdescripti"
                    f"on%2Centities%2Cid%2Clocation%2Cname%2Cpinn"
                    f"ed_tweet_id%2Cprofile_image_url%2Cprotecte"
                    f"d%2Curl%2Cusername%2Cverified%2Cwithhe"
                    f"ld&expansions=pinned_tweet_id&tweet."
                    f"fields=attachments%2Cauthor_id%2C"
                    f"context_annotations%2Cconversatio"
                    f"n_id%2Ccreated_at%2Centities%2Cgeo%2Cid%2Cin"
                    f"_reply_to_user_id%2Clang%2Cpublic_metrics"
                    f"%2Cpossibly_sensitive%2C"
                    f"referenced_tweets%2Csource%2Ctext%2Cwithheld"
                )
                mock.get(f"{sample_user_obj.twitter_base_url_v2}/users/by/"
                         f"username/{t_user}",
                         status_code=500)
                with pytest.raises(err_ex) as error_info:
                    sample_user_obj._get_twitter_info()
                exception_value = (
                    f"500 Server Error: None for url: {url_username}"
                )
                assert str(error_info.value) == exception_value


def test_main_oauth_exception(
        rootdir, global_mock, sample_users, mock_request, monkeypatch, caplog
):
    test_user = UserTemplate()
    with global_mock as g_mock:
        test_files_dir = os.path.join(rootdir, 'test_files')

        config_test = os.path.join(test_files_dir, 'config_multiple_users.yml')
        prev_config = os.path.join(os.getcwd(), 'config.yml')
        backup_config = os.path.join(os.getcwd(), 'config.yml.bak')
        if os.path.isfile(prev_config):
            shutil.copy(prev_config, backup_config)
        shutil.copy(config_test, prev_config)

        users_path = os.path.join(os.getcwd(), 'users')
        shutil.rmtree(users_path)

        g_mock.get(f"{test_user.twitter_base_url_v2}/users/2244994945"
                   f"/tweets",
                   json={},
                   status_code=200)

        monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
        with patch.object(sys, 'argv', ['']):
            with caplog.at_level(logging.ERROR):
                assert cli.main() == 0
                err_msg = (
                    "Unable to retrieve tweets. Is the account protected? "
                    "If so, you need to provide the following OAuth 1.0a "
                    "fields in the user config:"
                )
                assert err_msg in caplog.text

        # Clean-up
        g_mock.get(f"{test_user.twitter_base_url_v2}/users/2244994945"
                   f"/tweets",
                   json=mock_request['sample_data']['tweets_v2'],
                   status_code=200)
        if os.path.isfile(backup_config):
            shutil.copy(backup_config, prev_config)
        for sample_user in sample_users:
            sample_user_obj = sample_user['user_obj']
            for t_user in sample_user_obj.twitter_username:
                idx = sample_user_obj.twitter_username.index(t_user)
                pinned_path = os.path.join(
                    os.getcwd(),
                    'users',
                    sample_user_obj.twitter_username[idx],
                    'pinned_id.txt'
                )
                pinned_pleroma = os.path.join(
                    os.getcwd(),
                    'users',
                    sample_user_obj.twitter_username[idx],
                    'pinned_id_pleroma.txt'
                )
                if os.path.isfile(pinned_path):
                    os.remove(pinned_path)
                if os.path.isfile(pinned_pleroma):
                    os.remove(pinned_pleroma)
    return g_mock


def test__get_instance_info_exception(sample_users):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            info_url = (
                f"{sample_user_obj.pleroma_base_url}/.well-known/nodeinfo"
            )
            fb_url = (
                f"{sample_user_obj.pleroma_base_url}/nodeinfo/2.0"
            )
            down_msg = "Instance under maintenance"
            mock.get(info_url, status_code=500)
            mock.get(fb_url, {}, status_code=500)
            with pytest.raises(Exception) as error_info:
                sample_user_obj._get_instance_info()
            exception_value = (
                "Instance response was not understood"
            )

            assert(
                exception_value in str(error_info.value)
            )

            mock.get(info_url, text=down_msg, status_code=200)
            with pytest.raises(ValueError) as error_info:
                sample_user_obj._get_instance_info()
            exception_value = (
                f"Instance response was not understood {down_msg}"
            )
            assert str(error_info.value) == exception_value
            mock.post(fb_url, text=down_msg, status_code=200)
            with pytest.raises(ValueError) as error_info:
                sample_user_obj._get_instance_info()
            exception_value = (
                f"Instance response was not understood {down_msg}"
            )
            assert str(error_info.value) == exception_value


def test__download_media_exception(sample_users, caplog):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            media_url = "https://mymock.media/img.jpg"
            mock.get(media_url, status_code=500)
            media = [{'url': media_url, 'type': 'image'}]
            tweet = None
            with pytest.raises(requests.exceptions.HTTPError) as error_info:
                sample_user_obj._download_media(media, tweet)
            exception_value = f"500 Server Error: None for url: {media_url}"
            assert str(error_info.value) == exception_value
            mock.get(media_url, status_code=404)
            tweet = {"id": "12345"}
            with caplog.at_level(logging.WARNING):
                sample_user_obj._download_media(media, tweet)
            warn_msg1 = "Media not found (404)"
            warn_msg2 = "Ignoring attachment and continuing..."
            assert warn_msg1 in caplog.text
            assert warn_msg2 in caplog.text


def test__expand_urls(sample_users, mock_request, caplog):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            fake_url = "https://cutt.ly/xg3TuY0"
            mock.head(fake_url, status_code=500)
            tweet = mock_request['sample_data']['pinned_tweet_3']['data']
            with caplog.at_level(logging.DEBUG):
                sample_user_obj._expand_urls(tweet)
            exception_value = f"Couldn't expand the url {fake_url}"
            assert exception_value in caplog.text


def test_locker():
    with pytest.raises(TimeoutLocker) as error_info:
        with Locker():
            with Locker():
                time.sleep(20)
    exception_value = (
        "The file lock '/tmp/pleroma_bot.lock' could not be acquired. Is "
        "another instance of pleroma-bot running?"
    )
    assert str(error_info.value) == exception_value
