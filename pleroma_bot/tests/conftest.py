import os
import yaml
import json
import pytest
import requests_mock
from pleroma_bot.cli import User


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def mock_request(rootdir):
    mock_return = {}
    twitter_base_url = 'http://api.twitter.com/1.1'
    twitter_base_url_v2 = 'https://api.twitter.com/2'
    sample_data_dir = os.path.join(rootdir, 'test_files', 'sample_data')
    sample_data = {}
    for file in os.listdir(sample_data_dir):
        data = os.path.join(sample_data_dir, file)
        with open(data, 'r', encoding='utf8') as f:
            sample_data[os.path.splitext(file)[0]] = json.load(f)

    with requests_mock.Mocker() as mock:
        mock.get(f"{twitter_base_url_v2}/tweets/search/recent", json=sample_data['tweets_v2'], status_code=200)
        mock.get(f"{twitter_base_url}/users/show.json", json=sample_data['twitter_info'], status_code=200)
        mock.get(f"{twitter_base_url}/statuses/show.json", json=sample_data['tweet'], status_code=200)
        mock.get(f"{twitter_base_url_v2}/tweets?ids=1323049466837032961&expansions=attachments.poll_ids&poll.fields"
                 f"=duration_minutes%2Coptions",
                 json=sample_data['poll'],
                 status_code=200)
        mock_return['mock'] = mock
        mock_return['sample_data'] = sample_data
        return mock_return


@pytest.fixture
def sample_users(rootdir, mock_request):
    users = []
    # twitter_base_url = 'http://api.twitter.com/1.1'
    twitter_base_url_v2 = 'https://api.twitter.com/2'
    with mock_request['mock'] as mock:
        configs_dir = os.path.join(rootdir, 'test_files')
        with open(os.path.join(configs_dir, 'config.yml'), 'r', encoding='utf8') as stream:
            config = yaml.safe_load(stream)
        user_dict = config['users']
        for user_item in user_dict:
            mock.get(f"{twitter_base_url_v2}/users/by/username/{user_item['twitter_username']}",
                     json=mock_request['sample_data']['pinned'],
                     status_code=200)
            mock.get(f"{config['pleroma_base_url']}/api/v1/accounts/{user_item['pleroma_username']}/statuses",
                     json=mock_request['sample_data']['pleroma_statuses'],
                     status_code=200)
            users.append({'user_obj': User(user_item, config), 'mock': mock})

        return users