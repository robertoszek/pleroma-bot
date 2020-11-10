import os
import shutil
import logging

from test_user import UserTemplate
from pleroma_bot import cli

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
