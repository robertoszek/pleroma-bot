import os
import sys
import shutil
import hashlib
import logging
import urllib.parse
from unittest.mock import patch
from datetime import datetime, timedelta
from urllib import parse
from test_user import UserTemplate
from conftest import get_config_users

from pleroma_bot import cli, User
from pleroma_bot._utils import random_string
from pleroma_bot._utils import guess_type


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
    test_user = UserTemplate()
    for sample_user in sample_users:
        user_obj = sample_user['user_obj']
        replace = user_obj.replace_vars_in_str(test_user.replace_str)
        assert replace == sample_user['user_obj'].twitter_url


def test_user_replace_vars_in_str_var(sample_users):
    """
    Check that replace_vars_in_str replaces the var_name with the var_value
    correctly
    """
    test_user = UserTemplate()
    for sample_user in sample_users:
        user_obj = sample_user['user_obj']
        replace = user_obj.replace_vars_in_str(
            test_user.replace_str,
            "twitter_url"
        )
        assert replace == sample_user['user_obj'].twitter_url


def test_replace_vars_in_str_local(monkeypatch, sample_users):
    """
    Check that replace_vars_in_str replaces the var_name with the var_value
    correctly
    """
    test_var = "test_var value"
    for sample_user in sample_users:
        user_obj = sample_user['user_obj']
        user_obj.test_var = test_var
        replace = user_obj.replace_vars_in_str("{{ test_var }}")
        assert replace == test_var


def test_replace_vars_in_str_global(sample_users):
    """
    Check that replace_vars_in_str replaces the var_name with the var_value
    correctly
    """
    test_var = "value_global"
    for sample_user in sample_users:
        user_obj = sample_user['user_obj']
        user_obj.replace_vars_in_str.__globals__.update({'test_var': test_var})
        replace = user_obj.replace_vars_in_str(
            "{{ test_var }}"
        )
    assert replace == test_var


def test_user_attrs(sample_users):
    """
    Check that test user matches sample data fed by the mock
    """
    test_user = UserTemplate()
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
            assert (
                sample_user_obj.twitter_base_url_v2 ==
                test_user.twitter_base_url_v2
            )
            assert sample_user_obj.nitter == test_user.nitter
            assert (
                sample_user_obj.get_pinned_tweet() ==
                sample_user_obj.pinned_tweet_id
            )
        return mock


def test_check_pinned_tweet(sample_users, mock_request):
    """
    Needs to test the following Previous - Current pin statuses:
        Pinned -> Pinned (same pin)
        Pinned -> Pinned (diff pin)
        Pinned -> None
        None   -> None
        None   -> Pinned
    """
    test_user = UserTemplate()
    # Pinned -> Pinned
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
            with open(pinned_file, "w") as f:
                f.write(test_user.pinned + "\n")
            sample_user_obj.check_pinned()
            pinned_path = os.path.join(os.getcwd(),
                                       'users',
                                       sample_user_obj.twitter_username,
                                       'pinned_id.txt')
            pinned_pleroma = os.path.join(os.getcwd(),
                                          'users',
                                          sample_user_obj.twitter_username,
                                          'pinned_id_pleroma.txt')
            with open(pinned_path, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == test_user.pinned

            # Pinned -> Pinned (different ID)
            pinned_url = (
                f"{test_user.twitter_base_url_v2}/users/by/username/"
                f"{sample_user_obj.twitter_username}"
            )
            mock.get(pinned_url,
                     json=mock_request['sample_data']['pinned_2'],
                     status_code=200)
            new_pin_id = sample_user_obj._get_pinned_tweet_id()
            sample_user_obj.pinned_tweet_id = new_pin_id
            pinned = sample_user_obj.pinned_tweet_id
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
                     json=mock_request['sample_data']['pinned_tweet_2'],
                     status_code=200)
            mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids={pinned}"
                     f"&expansions=attachments.poll_ids"
                     f"&poll.fields=duration_minutes%2Coptions",
                     json=mock_request['sample_data']['poll_2'],
                     status_code=200)
            sample_user_obj.check_pinned()
            with open(pinned_path, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == test_user.pinned_2
            id_pleroma = test_user.pleroma_pinned
            with open(pinned_pleroma, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == id_pleroma

            # Pinned -> None
            mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/"
                     f"{sample_user_obj.twitter_username}",
                     json=mock_request['sample_data']['no_pinned'],
                     status_code=200)
            new_pin_id = sample_user_obj._get_pinned_tweet_id()
            sample_user_obj.pinned_tweet_id = new_pin_id
            sample_user_obj.check_pinned()
            with open(pinned_path, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == ''
            with open(pinned_pleroma, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == ''
            history = mock.request_history
            unpin_url = (
                f"{sample_user_obj.pleroma_base_url}"
                f"/api/v1/statuses/{test_user.pleroma_pinned}/unpin"
            )
            assert unpin_url == history[-1].url

            # None -> None
            sample_user_obj.check_pinned()
            with open(pinned_path, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == ''
            with open(pinned_pleroma, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == ''

            # None -> Pinned
            pinned_url = (
                f"{test_user.twitter_base_url_v2}/users/by/username/"
                f"{sample_user_obj.twitter_username}"
            )
            mock.get(pinned_url,
                     json=mock_request['sample_data']['pinned'],
                     status_code=200)
            new_pin_id = sample_user_obj._get_pinned_tweet_id()
            sample_user_obj.pinned_tweet_id = new_pin_id
            pinned = sample_user_obj.pinned_tweet_id
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
            sample_user_obj.check_pinned()
            with open(pinned_path, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == test_user.pinned
            id_pleroma = test_user.pleroma_pinned
            with open(pinned_pleroma, 'r', encoding='utf8') as f:
                assert f.readline().rstrip() == id_pleroma
            os.remove(pinned_path)
            os.remove(pinned_pleroma)


def test_get_date_last_pleroma_post(sample_users):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            date = sample_user_obj.get_date_last_pleroma_post()
            ts = datetime.strptime(str(date), "%Y-%m-%dT%H:%M:%S.%fZ")
    return ts, mock


def test_get_date_last_pleroma_post_no_posts(
        sample_users, caplog, monkeypatch
):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']

            url_statuses = (
                f"{test_user.pleroma_base_url}"
                f"/api/v1/accounts/"
                f"{sample_user_obj.pleroma_username}/statuses"
            )
            mock.get(url_statuses, json={}, status_code=200)
            with caplog.at_level(logging.WARNING):
                sample_user_obj.first_time = False
                date = sample_user_obj.get_date_last_pleroma_post()
            warning_msg = 'No posts were found in the target Fediverse account'
            assert warning_msg in caplog.text
            with caplog.at_level(logging.WARNING):
                sample_user_obj.first_time = True
                monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
                date = sample_user_obj.get_date_last_pleroma_post()
            warning_msg = 'No posts were found in the target Fediverse account'
            assert warning_msg in caplog.text
    return date


def test_guess_type(rootdir):
    """
    Test the guess_type functiona against different MIME types
    """
    test_files_dir = os.path.join(rootdir, 'test_files')
    sample_data_dir = os.path.join(test_files_dir, 'sample_data')
    media_dir = os.path.join(sample_data_dir, 'media')
    png = os.path.join(media_dir, 'image.png')
    svg = os.path.join(media_dir, 'image.svg')
    mp4 = os.path.join(media_dir, 'video.mp4')
    gif = os.path.join(media_dir, "animated_gif.gif")
    assert 'image/png' == guess_type(png)
    assert 'image/svg+xml' == guess_type(svg)
    assert 'video/mp4' == guess_type(mp4)
    assert 'image/gif' == guess_type(gif)


def test_get_twitter_info(mock_request, sample_users):
    """
    Check that _get_twitter_info retrieves the correct profile image and banner
    URLs
    """
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            twitter_info = mock_request['sample_data']['twitter_info']
            banner_url = f"{twitter_info['profile_banner_url']}/1500x500"
            profile_pic_url = twitter_info['profile_image_url_https']

            sample_user_obj._get_twitter_info()

            p_banner_url = sample_user_obj.profile_banner_url
            p_image_url = sample_user_obj.profile_image_url
            assert banner_url == p_banner_url
            assert profile_pic_url == p_image_url
    return mock


def test_update_pleroma(sample_users, rootdir):
    """
    Check that update_pleroma downloads the correct profile image and banner
    """
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
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

            sample_user_obj.update_pleroma()

            t_profile_banner = open(sample_user_obj.header_path, 'rb')
            t_profile_banner_content = t_profile_banner.read()
            t_profile_banner.close()

            t_profile_image = open(sample_user_obj.avatar_path, 'rb')
            t_profile_image_content = t_profile_image.read()
            t_profile_image.close()
            assert t_profile_banner_content == profile_banner_content
            assert t_profile_image_content == profile_image_content
    return mock


def test_post_pleroma_media(rootdir, sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            if sample_user_obj.media_upload:
                test_files_dir = os.path.join(rootdir, 'test_files')
                sample_data_dir = os.path.join(test_files_dir, 'sample_data')
                media_dir = os.path.join(sample_data_dir, 'media')
                png = os.path.join(media_dir, 'image.png')
                svg = os.path.join(media_dir, 'image.svg')
                mp4 = os.path.join(media_dir, 'video.mp4')
                gif = os.path.join(media_dir, "animated_gif.gif")
                tweet_folder = os.path.join(
                    sample_user_obj.tweets_temp_path, test_user.pinned
                )
                shutil.copy(png, tweet_folder)
                shutil.copy(svg, tweet_folder)
                shutil.copy(mp4, tweet_folder)
                shutil.copy(gif, tweet_folder)
                attach_number = len(os.listdir(tweet_folder))
                sample_user_obj.post_pleroma(
                    (test_user.pinned, "", ""), None, False
                )

                history = mock.request_history
                post_url = (
                    f"{sample_user_obj.pleroma_base_url}/api/v1/statuses"
                )
                assert post_url == history[-1].url
                token_sample = sample_user_obj.header_pleroma['Authorization']
                config_users = get_config_users('config.yml')
                users = config_users['user_dict']
                for user in users:
                    if (
                        user['pleroma_username']
                        == sample_user_obj.pleroma_username
                    ):
                        token_config = user['pleroma_token']

                assert f"Bearer {token_config}" == token_sample
                assert token_sample == history[-1].headers['Authorization']
                mock_media = mock_request['sample_data']['pleroma_post_media']
                id_media = mock_media['id']
                assert id_media in history[-1].text
                dict_history = urllib.parse.parse_qs(history[-1].text)
                assert len(dict_history['media_ids[]']) == attach_number
                for media in dict_history['media_ids[]']:
                    assert media == id_media

                for media_file in os.listdir(tweet_folder):
                    os.remove(os.path.join(tweet_folder, media_file))


def test_get_tweets(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            tweets_v2 = sample_user_obj._get_tweets("v2")
            assert tweets_v2 == mock_request['sample_data']['tweets_v2']
            tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
            assert tweet == mock_request['sample_data']['tweet']
            tweets = sample_user_obj._get_tweets("v1.1")
            assert tweets == mock_request['sample_data']['tweets_v1']
    return mock


def test_get_tweets_next_token(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            mock.get(f"{test_user.twitter_base_url_v2}/users/2244994945"
                     f"/tweets",
                     json=mock_request['sample_data']['tweets_v2_next_token'],
                     status_code=200)
            sample_user_obj = sample_user['user_obj']
            tweets_v2 = sample_user_obj._get_tweets("v2")
            assert 10 == len(tweets_v2["data"])

            mock.get(f"{test_user.twitter_base_url_v2}/users/2244994945"
                     f"/tweets",
                     json=mock_request['sample_data']['tweets_v2_next_token2'],
                     status_code=200)

            sample_user_obj = sample_user['user_obj']
            tweets_v2 = sample_user_obj._get_tweets("v2")
            assert 10 == len(tweets_v2["data"])
    return mock


def test_process_tweets(rootdir, sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            tweets_v2 = sample_user_obj._get_tweets("v2")
            assert tweets_v2 == mock_request['sample_data']['tweets_v2']
            tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
            assert tweet == mock_request['sample_data']['tweet']
            tweets = sample_user_obj._get_tweets("v1.1")
            assert tweets == mock_request['sample_data']['tweets_v1']
            test_files_dir = os.path.join(rootdir, 'test_files')
            sample_data_dir = os.path.join(test_files_dir, 'sample_data')
            media_dir = os.path.join(sample_data_dir, 'media')
            mp4 = os.path.join(media_dir, 'video.mp4')
            gif = os.path.join(media_dir, "animated_gif.gif")
            png = os.path.join(media_dir, 'image.png')

            gif_file = open(gif, 'rb')
            gif_content = gif_file.read()
            gif_hash = hashlib.sha256(gif_content).hexdigest()
            gif_file.close()

            png_file = open(png, 'rb')
            png_content = png_file.read()
            png_hash = hashlib.sha256(png_content).hexdigest()
            png_file.close()

            mp4_file = open(mp4, 'rb')
            mp4_content = mp4_file.read()
            mp4_hash = hashlib.sha256(mp4_content).hexdigest()
            mp4_file.close()

            tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

            for tweet in tweets_to_post['data']:
                # Test poll retrieval
                if tweet['id'] == test_user.pinned:
                    poll = mock_request['sample_data']['poll']
                    options = poll['includes']['polls'][0]['options']
                    duration = poll['includes']['polls'][0]['duration_minutes']
                    assert len(tweet['polls']['options']) == len(options)
                    assert tweet['polls']['expires_in'] == duration * 60
                # Test download
                tweet_folder = os.path.join(
                    sample_user_obj.tweets_temp_path, tweet["id"]
                )
                dict_hash = {
                    '0.mp4': mp4_hash,
                    '0.png': png_hash,
                    '0.gif': gif_hash
                }
                for file in os.listdir(tweet_folder):
                    file_path = os.path.join(tweet_folder, file)
                    if os.path.isfile(file_path):
                        f = open(file_path, 'rb')
                        file_content = f.read()
                        file_hash = hashlib.sha256(file_content).hexdigest()
                        f.close()
                        assert file_hash == dict_hash[file]
                        os.remove(file_path)
    return mock


def test_include_rts(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            config_users = get_config_users('config_norts.yml')
            for user_item in config_users['user_dict']:
                sample_user_obj = User(
                    user_item, config_users['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                retweet_found = False
                for tweet in tweets_to_post['data']:
                    if not sample_user_obj.include_rts:
                        assert not tweet["text"].startswith("RT")
                    if tweet["text"].startswith("RT"):
                        retweet_found = True
                    # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                if retweet_found:
                    assert sample_user_obj.include_rts
    return mock


def test_include_replies(sample_users, mock_request):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            config_users = get_config_users('config_noreplies.yml')
            for user_item in config_users['user_dict']:
                sample_user_obj = User(
                    user_item, config_users['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                reply_found = False

                for tweet in tweets_to_post['data']:
                    if not sample_user_obj.include_replies:
                        if (
                                hasattr(sample_user_obj, "rich_text")
                                and sample_user_obj.rich_text
                        ):
                            assert not tweet["text"].startswith("[@")
                        else:
                            assert not tweet["text"].startswith("@")
                    try:
                        for reference in tweet["referenced_tweets"]:
                            if reference["type"] == "replied_to":
                                reply_found = True
                                break
                    except KeyError:
                        pass
                    if (
                            tweet["text"].startswith("@")
                            or tweet["text"].startswith("[@")
                    ):
                        reply_found = True
                    # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                if reply_found:
                    assert sample_user_obj.include_replies
    return mock


def test_delay_post(sample_users, global_mock):
    for sample_user in sample_users:
        with global_mock as mock:
            users = get_config_users('config_delay_post.yml')

            for user_item in users['user_dict']:
                delay_post = users['config']['delay_post']
                sample_user_obj = User(
                    user_item, users['config'], os.getcwd()
                )
                assert delay_post == sample_user_obj.delay_post

    return mock, sample_user


def test_hashtags(sample_users, global_mock):
    for sample_user in sample_users:
        with global_mock as mock:
            users = get_config_users('config_hashtags.yml')

            for user_item in users['user_dict']:
                sample_user_obj = User(
                    user_item, users['config'], os.getcwd()
                )
                if sample_user_obj.hashtags:
                    tweets_v2 = sample_user_obj._get_tweets("v2")
                    tweets_to_post = sample_user_obj.process_tweets(tweets_v2)
                    for tweet in tweets_to_post['data']:
                        tweet_hashtags = tweet["entities"]["hashtags"]
                        i = 0
                        while i < len(tweet_hashtags):
                            if (
                                    tweet_hashtags[i]["tag"]
                                    in sample_user_obj.hashtags
                            ):
                                match = True
                                break
                            i += 1
                        else:
                            match = False

                        assert match

                        # Clean up
                        tweet_folder = os.path.join(
                            sample_user_obj.tweets_temp_path, tweet["id"]
                        )
                        for file in os.listdir(tweet_folder):
                            file_path = os.path.join(tweet_folder, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)

    return mock, sample_user


def test_nitter_instances(sample_users, mock_request, global_mock):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with global_mock as mock:
            users_nitter_net = get_config_users('config_nitter_global.yml')
            users_nitter = get_config_users(
                'config_nitter_different_instance.yml'
            )

            for user_item in users_nitter_net['user_dict']:
                nitter_instance = users_nitter_net['config']['nitter_base_url']
                sample_user_obj = User(
                    user_item, users_nitter_net['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                for tweet in tweets_to_post['data']:
                    if sample_user_obj.signature:
                        sample_user_obj.post_pleroma(
                            (
                                tweet["id"],
                                tweet["text"],
                                tweet["created_at"],
                            ), None, False
                        )
                        history = mock.request_history
                        assert nitter_instance in parse.unquote(
                            history[-1].text
                        )

                        # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

            for user_item in users_nitter['user_dict']:
                nitter_instance = users_nitter['config']['nitter_base_url']
                sample_user_obj = User(
                    user_item, users_nitter['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                for tweet in tweets_to_post['data']:
                    if sample_user_obj.signature:
                        sample_user_obj.post_pleroma(
                            (
                                tweet["id"],
                                tweet["text"],
                                tweet["created_at"]
                            ), None, False
                        )
                        history = mock.request_history
                        assert nitter_instance in parse.unquote(
                            history[-1].text
                        )

                    # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
    return mock, sample_user


def test_original_date(sample_users, mock_request, global_mock):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with global_mock as mock:
            users_date = get_config_users('config_original_date.yml')
            users_no_date = get_config_users('config_no_original_date.yml')

            for user_item in users_date['user_dict']:
                sample_user_obj = User(
                    user_item, users_date['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                for tweet in tweets_to_post['data']:
                    if sample_user_obj.signature:
                        sample_user_obj.post_pleroma(
                            (
                                tweet["id"],
                                tweet["text"],
                                tweet["created_at"],
                            ), None, False
                        )
                        history = mock.request_history
                        tweet_date = tweet["created_at"]
                        date_format = sample_user_obj.original_date_format
                        date = datetime.strftime(
                            datetime.strptime(
                                tweet_date, "%Y-%m-%dT%H:%M:%S.000Z"
                            ),
                            date_format,
                        )
                        assert f"[{date}]" in parse.unquote(
                            history[-1].text.replace("+", " ")
                        )

                        # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

            for user_item in users_no_date['user_dict']:
                sample_user_obj = User(
                    user_item, users_date['config'], os.getcwd()
                )
                tweets_v2 = sample_user_obj._get_tweets("v2")
                assert tweets_v2 == mock_request['sample_data']['tweets_v2']
                tweet = sample_user_obj._get_tweets("v1.1", test_user.pinned)
                assert tweet == mock_request['sample_data']['tweet']
                tweets = sample_user_obj._get_tweets("v1.1")
                assert tweets == mock_request['sample_data']['tweets_v1']

                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)

                for tweet in tweets_to_post['data']:
                    if sample_user_obj.signature:
                        sample_user_obj.post_pleroma(
                            (
                                tweet["id"],
                                tweet["text"],
                                tweet["created_at"],
                            ), None, False
                        )
                        history = mock.request_history
                        tweet_date = tweet["created_at"]
                        date_format = sample_user_obj.original_date_format
                        date = datetime.strftime(
                            datetime.strptime(
                                tweet_date, "%Y-%m-%dT%H:%M:%S.000Z"
                            ),
                            date_format,
                        )
                        assert f"[{date}]" not in parse.unquote(
                            history[-1].text.replace("+", " ")
                        )

                        # Clean up
                    tweet_folder = os.path.join(
                        sample_user_obj.tweets_temp_path, tweet["id"]
                    )
                    for file in os.listdir(tweet_folder):
                        file_path = os.path.join(tweet_folder, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
    return mock, sample_user


def test__process_polls_with_media(sample_users):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            media_url = "https://mymock.media/img.jpg"
            mock.get(media_url, status_code=500)
            media = [{'url': media_url, 'type': 'image'}]
            tweet = {'attachments': {'poll_ids': 123}}
            polls = sample_user_obj._process_polls(tweet, media)
            assert polls is None


def test_force_date(sample_users, monkeypatch):
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
            date = sample_user_obj.force_date()
            assert date == '2020-12-30T00:00:00Z'
            monkeypatch.setattr('builtins.input', lambda: None)
            date = sample_user_obj.force_date()
            assert date == '2010-11-06T00:00:00Z'
            sample_user_obj.posts = 'none_found'
            monkeypatch.setattr('builtins.input', lambda: "continue")
            date = sample_user_obj.force_date()
            ts = datetime.strftime(
                datetime.now() - timedelta(days=2), "%Y-%m-%dT%H:%M:%SZ"
            )
            assert date == ts
            sample_user_obj.posts = None
            mock.get(f"{sample_user_obj.pleroma_base_url}"
                     f"/api/v1/accounts/"
                     f"{sample_user_obj.pleroma_username}/statuses",
                     json={},
                     status_code=200)
            monkeypatch.setattr('builtins.input', lambda: "continue")
            date = sample_user_obj.force_date()
            assert date == sample_user_obj.get_date_last_pleroma_post()

    return mock


def test_main(rootdir, global_mock, sample_users, monkeypatch):
    with global_mock as g_mock:
        test_files_dir = os.path.join(rootdir, 'test_files')

        config_test = os.path.join(test_files_dir, 'config_multiple_users.yml')
        config_tweet_ids = os.path.join(test_files_dir, 'config_tweet_ids.yml')
        prev_config = os.path.join(os.getcwd(), 'config.yml')
        backup_config = os.path.join(os.getcwd(), 'config.yml.bak')
        if os.path.isfile(prev_config):
            shutil.copy(prev_config, backup_config)
        shutil.copy(config_test, prev_config)

        users_path = os.path.join(os.getcwd(), 'users')
        shutil.rmtree(users_path)

        parent_config = os.path.join(
            os.getcwd(), os.pardir, 'config.yml'
        )
        if os.path.isfile(config_test):
            shutil.copy(config_test, parent_config)
        monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
        with patch.object(sys, 'argv', ['', '--config', '../config.yml']):
            assert cli.main() == 0

        with patch.object(sys, 'argv', ['', '--config', config_tweet_ids]):
            assert cli.main() == 0

        monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
        with patch.object(sys, 'argv', ['', '--skipChecks', '-v']):
            assert cli.main() == 0

        monkeypatch.setattr('builtins.input', lambda: "2020-12-30")
        with patch.object(sys, 'argv', ['']):
            assert cli.main() == 0
        # Test main() is called correctly when name equals __main__
        with patch.object(cli, "main", return_value=42):
            with patch.object(cli, "__name__", "__main__"):
                with patch.object(cli.sys, 'exit') as mock_exit:
                    with patch.object(
                            sys, 'argv', ['', '--log', '../error.log']
                    ):
                        cli.init()
                        assert mock_exit.call_args[0][0] == 42
        with patch.object(cli, "main", return_value=42):
            with patch.object(cli, "__name__", "__main__"):
                with patch.object(cli.sys, 'exit') as mock_exit:
                    with patch.object(
                            sys, 'argv', ['', '--config', 'config.yml']
                    ):
                        cli.init()
                        assert mock_exit.call_args[0][0] == 42
        with patch.object(cli, "main", return_value=42):
            with patch.object(cli, "__name__", "__main__"):
                with patch.object(cli.sys, 'exit') as mock_exit:
                    cli.init()
                    assert mock_exit.call_args[0][0] == 42

        # Clean-up
        if os.path.isfile(backup_config):
            shutil.copy(backup_config, prev_config)
        for sample_user in sample_users:
            sample_user_obj = sample_user['user_obj']
            pinned_path = os.path.join(os.getcwd(),
                                       'users',
                                       sample_user_obj.twitter_username,
                                       'pinned_id.txt')
            pinned_pleroma = os.path.join(os.getcwd(),
                                          'users',
                                          sample_user_obj.twitter_username,
                                          'pinned_id_pleroma.txt')
            if os.path.isfile(pinned_path):
                os.remove(pinned_path)
            if os.path.isfile(pinned_pleroma):
                os.remove(pinned_pleroma)
    return g_mock
