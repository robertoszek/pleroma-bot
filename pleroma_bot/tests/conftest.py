import os
import re

import yaml
import json
import pytest
import requests
import requests_mock

from test_user import UserTemplate
from pleroma_bot.cli import User


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def mock_request(rootdir):
    test_user = UserTemplate()
    mock_return = {}
    twitter_base_url = test_user.twitter_base_url
    twitter_base_url_v2 = test_user.twitter_base_url_v2
    pleroma_base_url = test_user.pleroma_base_url
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
        mock.get(f"{pleroma_base_url}/api/v1/instance",
                 json={'version': '2.7.2 (compatible; Pleroma 2.2.1)'},
                 status_code=200)
        mock.get(f"{pleroma_base_url}/.well-known/nodeinfo",
                 json=sample_data["nodeinfo"],
                 status_code=200)
        mock.get(f"{pleroma_base_url}/nodeinfo/2.0",
                 json=sample_data["2_0"],
                 status_code=200)
        mock.get(
            "https://cutt.ly/xg3TuY0",
            status_code=301,
            headers={'Location': 'http://github.com'}
        )
        mock.head(
            "https://cutt.ly/xg3TuY0",
            status_code=301,
            headers={'Location': 'http://github.com'}
        )
        mock.head(
            "http://cutt.ly/xg3TuY0",
            status_code=301,
            headers={'Location': 'http://github.com'}
        )

        mock.head(
            "http://cutt.ly/xg3TuYA",
            status_code=301,
            headers={
                'Location': 'https://twitter.com/BotPleroma/status'
                            '/1474760145850806283/video/1'
            }
        )
        mock.head(
            'https://twitter.com/BotPleroma/status'
            '/1474760145850806283/video/1',
            status_code=200,
            headers={
                'Location': 'https://twitter.com/BotPleroma/status'
                            '/1474760145850806283/video/1'
            }
        )

        empty_resp = requests.packages.urllib3.response.HTTPResponse()
        mock.head(
            "https://twitter.com/BotPleroma/status/1323048312161947650"
            "/photo/1",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "http://twitter.com/BotPleroma/status/1323048312161947650"
            "/photo/1",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "https://twitter.com/BotPleroma/status/111242346465757545"
            "/video/1",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "https://twitter.com/BotPleroma/status/"
            "111242346465757545/video/10",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "https://twitter.com/BotPleroma/status/"
            "1323049214134407171/video/1",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            status_code=200,
            raw=empty_resp,
        )
        mock.head(
            "https://twitter.com/BotPleroma/status/1323049214134407171",
            status_code=200,
            raw=empty_resp,
        )
        mock.head("http://github.com", raw=empty_resp, status_code=200)
        mock.get(f"{twitter_base_url}/statuses/show.json",
                 json=sample_data['tweet'],
                 status_code=200)
        mock_return['mock'] = mock
        mock_return['sample_data'] = sample_data
        return mock_return


@pytest.fixture
def _sample_users(mock_request, rootdir):
    users = []
    test_user = UserTemplate()
    twitter_base_url_v2 = test_user.twitter_base_url_v2
    with mock_request['mock'] as mock:
        config_users = get_config_users('config.yml')
        for user_item in config_users['user_dict']:
            pinned = test_user.pinned
            pinned2 = test_user.pinned_2

            mock.get("https://api.twitter.com/2/tweets/1339829031147954177"
                     "?poll.fields=duration_minutes%2Cend_datetime%2Cid"
                     "%2Coptions%2Cvoting_status&media.fields=duration_ms"
                     "%2Cheight%2Cmedia_key%2Cpreview_image_url%2Ctype%2Curl"
                     "%2Cwidth%2Cpublic_metrics&expansions=attachments"
                     ".poll_ids%2Cattachments.media_keys%2Cauthor_id"
                     "%2Centities.mentions.username%2Cgeo.place_id"
                     "%2Cin_reply_to_user_id%2Creferenced_tweets.id"
                     "%2Creferenced_tweets.id.author_id&tweet.fields"
                     "=attachments%2Cauthor_id%2Ccontext_annotations"
                     "%2Cconversation_id%2Ccreated_at%2Centities%2Cgeo%2Cid"
                     "%2Cin_reply_to_user_id%2Clang%2Cpublic_metrics"
                     "%2Cpossibly_sensitive%2Creferenced_tweets%2Csource"
                     "%2Ctext%2Cwithheld",
                     json=mock_request['sample_data']['pinned_tweet'],
                     status_code=200)
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
            mock.get(f"{test_user.twitter_base_url_v2}/tweets/{pinned2}"
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
            user_v2 = f"user_v2_{user_item['twitter_username']}"
            mock.get(f"{twitter_base_url_v2}/users/by/username/"
                     f"{user_item['twitter_username']}",
                     json=mock_request['sample_data'][user_v2],
                     status_code=200)
            mock.get(f"{twitter_base_url_v2}/users/by?"
                     f"usernames={user_item['twitter_username']}",
                     json=mock_request['sample_data']['user_id'],
                     status_code=200)

            mock.get(f"{test_user.twitter_base_url_v2}/users/by/username/"
                     f"{user_item['twitter_username']}",
                     json=mock_request['sample_data'][user_v2],
                     status_code=200)

            mock.get(f"{test_user.twitter_base_url}/users/"
                     f"show.json?screen_name={user_item['twitter_username']}",
                     json=mock_request['sample_data']['twitter_info'],
                     status_code=200)

            mock.get(f"{test_user.twitter_base_url_v2}/users/2244994945"
                     f"/tweets",
                     json=mock_request['sample_data']['tweets_v2'],
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
            mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids="
                     f"{test_user.pinned}&expansions=attachments.poll_ids"
                     f"&poll.fields=duration_minutes%2Coptions",
                     json=mock_request['sample_data']['poll'],
                     status_code=200)
            mock.get(f"{test_user.twitter_base_url_v2}/tweets?ids="
                     f"{test_user.pinned_2}&expansions=attachments.poll_ids"
                     f"&poll.fields=duration_minutes%2Coptions",
                     json=mock_request['sample_data']['poll'],
                     status_code=200)
            mock.get(f"{config_users['config']['pleroma_base_url']}"
                     f"/api/v1/accounts/"
                     f"{user_item['pleroma_username']}/statuses",
                     json=mock_request['sample_data']['pleroma_statuses'],
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
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/meta",
                      json={},
                      status_code=500)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/i",
                      json=mock_request['sample_data']['misskey_i'],
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/users/notes",
                      json=mock_request['sample_data']['misskey_notes'],
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/drive/files/create",
                      json={"id": 12345},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/drive/files/update",
                      json={"id": 12345},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/i/update",
                      json={"id": 12345},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/notes/create",
                      json={"createdNote": {"id": 12345}},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/users/show",
                      json={"pinnedNoteIds": [12345]},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/i/pin",
                      json={"id": test_user.pleroma_pinned},
                      status_code=200)
            mock.post(f"{config_users['config']['pleroma_base_url']}"
                      f"/api/i/unpin",
                      json={"id": 12345},
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
            mock.get("https://twitter.com/BotPleroma/status"
                     "/1323048312161947650/photo/1",
                     content=png_content,
                     headers={'Content-Type': 'image/png'},
                     status_code=200)
            mock.get("https://pbs.twimg.com/media/ElxpP0hXEAI9X-H.jpg",
                     content=png_content,
                     headers={'Content-Type': 'image/png'},
                     status_code=200)
            mock.get(f"{test_user.twitter_base_url}/statuses/show.json?"
                     f"id=1323049214134407171",
                     json=mock_request['sample_data']['tweet_video'],
                     status_code=200)
            mock.get("https://twitter.com/BotPleroma/status"
                     "/1474760145850806283/video/1",
                     content=mp4_content,
                     headers={'Content-Type': 'video/mp4'},
                     status_code=200)
            mock.get("https://twitter.com/BotPleroma/status"
                     "1323049214134407171/video/1",
                     content=mp4_content,
                     headers={'Content-Type': 'video/mp4'},
                     status_code=200)

            mock.get("https://video.twimg.com/ext_tw_video/1323049175848833033"
                     "/pu/vid/1280x720/de6uahiosn3VXMZO.mp4?tag=10",
                     content=mp4_content,
                     headers={'Content-Type': 'video/mp4'},
                     status_code=200)

            twitter_info = mock_request['sample_data']['twitter_info']
            banner_url = f"{twitter_info['profile_banner_url']}/1500x500"
            mock.get(f"{banner_url}",
                     content=profile_banner_content,
                     status_code=200)
            profile_pic_url = twitter_info['profile_image_url_https']
            profile_img_big = re.sub(
                r"normal", "400x400", profile_pic_url
            )
            mock.get(twitter_info["profile_image_url"],
                     content=profile_image_content,
                     status_code=200)
            mock.get(f"{profile_img_big}",
                     content=profile_image_content,
                     status_code=200)
            mock.patch(f"{config_users['config']['pleroma_base_url']}"
                       f"/api/v1/accounts/update_credentials",
                       status_code=200)
            try:
                max_tweets = user_item['max_tweets']
            except KeyError:
                max_tweets = config_users['config']['max_tweets']

            mock.get(f"{config_users['config']['twitter_base_url']}"
                     f"/statuses/user_timeline.json?screen_name="
                     f"{user_item['twitter_username']}&count="
                     f"{max_tweets}&include_rts=true",
                     json=mock_request['sample_data']['tweets_v1'],
                     status_code=200)

            users.append(
                {
                    'user_obj': User(
                        user_item, config_users['config'], os.getcwd()
                    ),
                    'mock': mock,
                    'config': config_users['config']}
            )
        sample_users = {'users': users, 'global_mock': mock}
        return sample_users


@pytest.fixture
def sample_users(_sample_users):
    return _sample_users['users']


@pytest.fixture
def global_mock(_sample_users):
    return _sample_users['global_mock']


def get_config_users(config):
    rootdir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(rootdir, 'test_files')
    with open(os.path.join(configs_dir, config), 'r',
              encoding='utf8') as stream:
        config = yaml.safe_load(stream)
    user_dict = config['users']
    return {'user_dict': user_dict, 'config': config}
