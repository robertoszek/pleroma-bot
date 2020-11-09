import os
import re

import yaml
import json
import pytest
import requests_mock

from test_user import TestUser
from pleroma_bot.cli import User


@pytest.fixture(scope="session")
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def mock_request(rootdir):
    test_user = TestUser()
    mock_return = {}
    twitter_base_url = test_user.twitter_base_url
    twitter_base_url_v2 = test_user.twitter_base_url_v2
    sample_data_dir = os.path.join(rootdir, 'test_files', 'sample_data')
    sample_data = {}
    for file in os.listdir(sample_data_dir):
        if os.path.isfile(os.path.join(sample_data_dir, file)):
            data = os.path.join(sample_data_dir, file)
            with open(data, 'r', encoding='utf8') as f:
                sample_data[os.path.splitext(file)[0]] = json.load(f)

    with requests_mock.Mocker() as mock:
        mock.get(f"{twitter_base_url_v2}/tweets/search/recent",
                 json=sample_data['tweets_v2'],
                 status_code=200)
        mock.get(f"{twitter_base_url}/users/show.json",
                 json=sample_data['twitter_info'],
                 status_code=200)
        mock.get(f"{twitter_base_url}/statuses/show.json",
                 json=sample_data['tweet'],
                 status_code=200)
        mock_return['mock'] = mock
        mock_return['sample_data'] = sample_data
        return mock_return


@pytest.fixture(scope="session")
def sample_users(mock_request, rootdir):
    users = []
    test_user = TestUser()
    twitter_base_url_v2 = test_user.twitter_base_url_v2
    with mock_request['mock'] as mock:
        config_users = get_config_users('config.yml')
        for user_item in config_users['user_dict']:
            mock.get(f"{twitter_base_url_v2}/users/by/username/"
                     f"{user_item['twitter_username']}",
                     json=mock_request['sample_data']['pinned'],
                     status_code=200)

            headers_statuses = {
                "link": f"<{config_users['config']['pleroma_base_url']}"
                        f"/api/v1/accounts/"
                        f"{user_item['pleroma_username']}/statuses/"
                        f'?limit=20&max_id={test_user.pleroma_pinned}>; '
                        f'rel="next", '
                        f"<{config_users['config']['pleroma_base_url']}"
                        f"/api/v1/accounts/"
                        f"{user_item['pleroma_username']}/statuses/"
                        f'?limit=20&max_id={test_user.pleroma_pinned}>; '
                        f'rel="prev"'
            }
            mock.get(f"{config_users['config']['pleroma_base_url']}"
                     f"/api/v1/accounts/"
                     f"{user_item['pleroma_username']}/statuses",
                     json=mock_request['sample_data']['pleroma_statuses_pin'],
                     headers=headers_statuses,
                     status_code=200)
            mock.get(f"{config_users['config']['pleroma_base_url']}"
                     f"/api/v1/accounts/"
                     f"{user_item['pleroma_username']}/statuses/"
                     f'?limit=20&max_id={test_user.pleroma_pinned}',
                     json=mock_request['sample_data']['pleroma_statuses_pin'],
                     headers=headers_statuses,
                     status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/v1/statuses",
                      headers=headers_statuses,
                      json=mock_request['sample_data']['pleroma_post'],
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/v1/media",
                      json=mock_request['sample_data']['pleroma_post_media'],
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/v1/statuses/{test_user.pleroma_pinned_new}/pin",
                      json=mock_request['sample_data']['pleroma_pin'],
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/v1/statuses/{test_user.pleroma_pinned}/unpin",
                      json=mock_request['sample_data']['pleroma_pin'],
                      status_code=200)

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

            twitter_info = mock_request['sample_data']['twitter_info']
            banner_url = twitter_info['profile_banner_url']
            mock.get(f"{banner_url}",
                     content=profile_banner_content,
                     status_code=200)
            profile_pic_url = twitter_info['profile_image_url_https']
            profile_img_big = re.sub(
                r"normal", "400x400", profile_pic_url
            )
            mock.get(f"{profile_img_big}",
                     content=profile_image_content,
                     status_code=200)
            mock.patch(f"{config_users['config']['pleroma_base_url']}"
                       f"/api/v1/accounts/update_credentials",
                       status_code=200)

            users.append({'user_obj': User(user_item, config_users['config']),
                          'mock': mock, 'config': config_users['config']})
        return users


def get_config_users(config):
    rootdir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(rootdir, 'test_files')
    with open(os.path.join(configs_dir, config), 'r',
              encoding='utf8') as stream:
        config = yaml.safe_load(stream)
    user_dict = config['users']
    return {'user_dict': user_dict, 'config': config}
