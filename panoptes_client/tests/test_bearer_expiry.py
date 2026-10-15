
from panoptes_client.panoptes import Panoptes
from panoptes_client.panoptes import PanoptesAPIException

import datetime
import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import Mock, patch
else:
    from unittest.mock import Mock, patch


class MockDate(datetime.datetime):

    _fake = None

    @classmethod
    def fake(cls, time):
        cls._fake = time

    @classmethod
    def now(cls, tz=None):
        return cls._fake


@patch('panoptes_client.panoptes.datetime', MockDate)
class TestBearer(unittest.TestCase):

    def test_early(self):
        target = datetime.datetime(2017, 1, 1, 10, 0, 0)
        MockDate.fake(target)

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.valid_bearer_token() is True

    def test_early_2(self):
        target = datetime.datetime(2017, 1, 1, 11, 58, 0)
        MockDate.fake(target)

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.valid_bearer_token() is True

    def test_late(self):
        target = datetime.datetime(2017, 1, 1, 14, 0, 0)
        MockDate.fake(target)

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.valid_bearer_token() is False

    def test_late_2(self):
        target = datetime.datetime(2017, 1, 1, 12, 0, 1)
        MockDate.fake(target)

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.valid_bearer_token() is False

    def test_in_buffer(self):
        target = datetime.datetime(2017, 1, 1, 11, 59, 0)
        MockDate.fake(target)

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.valid_bearer_token() is False

    def test_has_token(self):
        client = Panoptes()
        client.bearer_token = True

        assert client.has_bearer_token() is True

    def test_has_no_token(self):
        client = Panoptes()

        assert client.has_bearer_token() is False

    def test_refresh_token_failure_retries_after_login(self):
        MockDate.fake(datetime.datetime(2017, 1, 1, 10, 0, 0))

        client = Panoptes()
        client.valid_bearer_token = Mock(return_value=False)
        client.username = 'user'
        client.password = 'password'
        client.logged_in = True
        client.bearer_token = 'expired'
        client.refresh_token = 'stale-refresh'

        refresh_response = Mock()
        refresh_response.json.return_value = {'error': 'invalid_grant'}
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'users': [{'id': '1'}]}
        token_response = Mock()
        token_response.json.return_value = {
            'access_token': 'new-token',
            'expires_in': 3600,
            'refresh_token': 'new-refresh',
        }
        csrf_response = Mock()
        csrf_response.headers = {'x-csrf-token': 'csrf-token'}
        client.session.get = Mock(return_value=csrf_response)
        client.session.post = Mock(side_effect=[
            refresh_response,
            login_response,
            token_response,
        ])

        assert client.get_bearer_token() == 'new-token'
        assert client.refresh_token == 'new-refresh'
        assert client.logged_in is True
        assert client.session.post.call_count == 3
        assert client.session.post.call_args_list[0][0][1]['grant_type'] == (
            'refresh_token'
        )
        assert client.session.post.call_args_list[2][0][1]['grant_type'] == (
            'password'
        )

    def test_missing_access_token_raises_api_exception_after_retry(self):
        MockDate.fake(datetime.datetime(2017, 1, 1, 10, 0, 0))

        client = Panoptes()
        client.valid_bearer_token = Mock(return_value=False)
        client.username = 'user'
        client.password = 'password'
        client.logged_in = True
        client.bearer_token = 'expired'
        client.refresh_token = 'stale-refresh'

        refresh_response = Mock()
        refresh_response.json.return_value = {'error': 'invalid_grant'}
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'users': [{'id': '1'}]}
        retry_response = Mock()
        retry_response.json.return_value = {'error': 'invalid_grant'}
        csrf_response = Mock()
        csrf_response.headers = {'x-csrf-token': 'csrf-token'}
        client.session.get = Mock(return_value=csrf_response)
        client.session.post = Mock(side_effect=[
            refresh_response,
            login_response,
            retry_response,
        ])

        with self.assertRaises(PanoptesAPIException):
            client.get_bearer_token()
