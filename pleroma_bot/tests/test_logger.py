import os
import shutil
import logging

from pleroma_bot import cli, User
from test_user import UserTemplate
from conftest import get_config_users

LOGGER = logging.getLogger(__name__)


def test_unpin_pleroma_logger(sample_users, mock_request, caplog):
    with caplog.at_level(logging.WARNING):
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
                    status_code=200
                )
                empty_file = os.path.join(os.getcwd(), 'empty.txt')
                open(empty_file, 'a').close()
                pinned_file = os.path.join(sample_user_obj.user_path,
                                           "pinned_id_pleroma.txt")
                shutil.copy(empty_file, pinned_file)
                sample_user_obj.unpin_pleroma(pinned_file)
                os.remove(pinned_file)
                os.remove(empty_file)
    assert 'Pinned post not found. Giving up unpinning...' in caplog.text


def test_main_exception_logger(global_mock, sample_users, caplog):
    with caplog.at_level(logging.ERROR):
        with global_mock as mock:
            prev_config = os.path.join(os.getcwd(), 'config.yml')
            backup_config = os.path.join(os.getcwd(), 'config.yml.bak')
            if os.path.isfile(prev_config):
                shutil.copy(prev_config, backup_config)

            assert cli.main() == 1

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
        mock.reset_mock()
    assert 'Exception occurred\nTraceback' in caplog.text


def test_post_pleroma_media_logger(rootdir, sample_users, caplog):
    test_user = UserTemplate()
    for sample_user in sample_users:
        with sample_user['mock'] as mock:
            sample_user_obj = sample_user['user_obj']
            if sample_user_obj.media_upload:
                test_files_dir = os.path.join(rootdir, 'test_files')
                sample_data_dir = os.path.join(
                    test_files_dir, 'sample_data'
                )

                media_dir = os.path.join(sample_data_dir, 'media')
                png = os.path.join(media_dir, 'image.png')
                svg = os.path.join(media_dir, 'image.svg')
                mp4 = os.path.join(media_dir, 'video.mp4')
                gif = os.path.join(media_dir, "animated_gif.gif")
                tweet_folder = os.path.join(
                    sample_user_obj.tweets_temp_path, test_user.pinned
                )
                os.makedirs(tweet_folder, exist_ok=True)
                shutil.copy(png, tweet_folder)
                shutil.copy(svg, tweet_folder)
                shutil.copy(mp4, tweet_folder)
                shutil.copy(gif, tweet_folder)

                media_url = (
                    f"{test_user.pleroma_base_url}/api/v1/media"
                )
                mock.post(media_url, status_code=513)
                with caplog.at_level(logging.ERROR):
                    sample_user_obj.post_pleroma(
                        (test_user.pinned, ""), None, False
                    )
                assert 'Exception occurred' in caplog.text
                assert 'Media size too large' in caplog.text

                for media_file in os.listdir(tweet_folder):
                    os.remove(os.path.join(tweet_folder, media_file))
                os.rmdir(tweet_folder)


def test_post_pleroma_media_size_logger(
        rootdir, mock_request, sample_users, caplog):
    test_user = UserTemplate()

    with mock_request['mock'] as mock:
        users_file_size = get_config_users('config_file_size.yml')

        for user_item in users_file_size['user_dict']:
            sample_user_obj = User(user_item, users_file_size['config'])
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
            gif_file.close()

            png_file = open(png, 'rb')
            png_content = png_file.read()
            png_file.close()

            mp4_file = open(mp4, 'rb')
            mp4_content = mp4_file.read()
            mp4_file.close()

            mock.get("https://video.twimg.com/tweet_video/ElxpatpX0AAFCLC.mp4",
                     content=gif_content,
                     headers={'Content-Type': 'image/gif'},
                     status_code=200)
            mock.get("https://pbs.twimg.com/media/ElxpP0hXEAI9X-H.jpg",
                     content=png_content,
                     headers={'Content-Type': 'image/png'},
                     status_code=200)
            mock.get(f"{test_user.twitter_base_url}/statuses/show.json?"
                     f"id=1323049214134407171",
                     json=mock_request['sample_data']['tweet_video'],
                     status_code=200)
            mock.get("https://video.twimg.com/ext_tw_video/1323049175848833033"
                     "/pu/vid/1280x720/de6uahiosn3VXMZO.mp4?tag=10",
                     content=mp4_content,
                     headers={'Content-Type': 'video/mp4'},
                     status_code=200)
            with caplog.at_level(logging.ERROR):
                tweets_to_post = sample_user_obj.process_tweets(tweets_v2)
            if hasattr(sample_user_obj, "file_max_size"):
                error_msg = (
                    f'Attachment exceeded config file size '
                    f'limit ({sample_user_obj.file_max_size})'
                )
                assert error_msg in caplog.text
                assert 'File size: 1.45MB' in caplog.text
                assert 'Ignoring attachment and continuing...' in caplog.text

            for tweet in tweets_to_post['data']:
                # Clean up
                tweet_folder = os.path.join(
                    sample_user_obj.tweets_temp_path, tweet["id"]
                )
                for file in os.listdir(tweet_folder):
                    file_path = os.path.join(tweet_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
