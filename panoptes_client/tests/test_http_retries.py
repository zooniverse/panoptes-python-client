import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

from panoptes_client.panoptes import (
    HTTP_RETRY_LIMIT,
    Panoptes,
    PanoptesAPIException,
)


class TestRetries(unittest.TestCase):
    def setUp(self):
        self.http_result = Mock()
        self.client = Panoptes()
        self.client.valid_bearer_token = Mock()
        self.client.valid_bearer_token.return_value = True
        self.client.bearer_token = '1234'
        self.client.session = Mock()
        self.client.session.request = Mock()
        self.client.session.request.return_value = self.http_result

    def assert_retry(self, *args, **kwargs):
        self.assertTrue(kwargs.get('retry', False))
        result = Mock()
        result.status_code = 204
        return result

    def assert_no_retry(self, *args, **kwargs):
        self.assertFalse(kwargs.get('retry', True))
        result = Mock()
        result.status_code = 204
        return result

    @patch('panoptes_client.panoptes.RETRY_BACKOFF_INTERVAL', 1)
    def test_request_retry_success(self):
        self.http_result.status_code = 200

        self.assertEqual(
            self.client.http_request('GET', '', retry=True),
            self.http_result,
        )
        self.assertEqual(
            self.client.session.request.call_count,
            1,
        )

    @patch('panoptes_client.panoptes.RETRY_BACKOFF_INTERVAL', 1)
    def test_request_retry_no_success(self):
        self.http_result.status_code = 500

        with self.assertRaises(PanoptesAPIException):
            self.assertEqual(
                self.client.http_request('GET', '', retry=True),
                self.http_result,
            )
        self.assertEqual(
            self.client.session.request.call_count,
            HTTP_RETRY_LIMIT,
        )

    @patch('panoptes_client.panoptes.RETRY_BACKOFF_INTERVAL', 1)
    def test_request_no_retry_success(self):
        self.http_result.status_code = 200

        self.assertEqual(
            self.client.http_request('GET', '', retry=False),
            self.http_result,
        )
        self.assertEqual(
            self.client.session.request.call_count,
            1,
        )

    @patch('panoptes_client.panoptes.RETRY_BACKOFF_INTERVAL', 1)
    def test_request_no_retry_no_success(self):
        self.http_result.status_code = 500

        with self.assertRaises(PanoptesAPIException):
            self.assertEqual(
                self.client.http_request('GET', '', retry=False),
                self.http_result,
            )
        self.assertEqual(
            self.client.session.request.call_count,
            1,
        )

    def test_json_retry(self):
        self.client.http_request = self.assert_retry
        self.client.json_request('', '', retry=True)

    def test_json_no_retry(self):
        self.client.http_request = self.assert_no_retry
        self.client.json_request('', '', retry=False)

    def test_get_retry(self):
        self.client.json_request = self.assert_retry
        self.client.get('', retry=True)

    def test_get_no_retry(self):
        self.client.json_request = self.assert_no_retry
        self.client.get('', retry=False)

    def test_get_request_retry(self):
        self.client.http_request = self.assert_retry
        self.client.get_request('', retry=True)

    def test_get_request_no_retry(self):
        self.client.http_request = self.assert_no_retry
        self.client.get_request('', retry=False)

    def test_put_retry(self):
        self.client.json_request = self.assert_retry
        self.client.put('', retry=True)

    def test_put_no_retry(self):
        self.client.json_request = self.assert_no_retry
        self.client.put('', retry=False)

    def test_put_request_retry(self):
        self.client.http_request = self.assert_retry
        self.client.put_request('', retry=True)

    def test_put_request_no_retry(self):
        self.client.http_request = self.assert_no_retry
        self.client.put_request('', retry=False)

    def test_post_retry(self):
        self.client.json_request = self.assert_retry
        self.client.post('', retry=True)

    def test_post_no_retry(self):
        self.client.json_request = self.assert_no_retry
        self.client.post('', retry=False)

    def test_post_request_retry(self):
        self.client.http_request = self.assert_retry
        self.client.post_request('', retry=True)

    def test_post_request_no_retry(self):
        self.client.http_request = self.assert_no_retry
        self.client.post_request('', retry=False)

    def test_delete_retry(self):
        self.client.json_request = self.assert_retry
        self.client.delete('', retry=True)

    def test_delete_no_retry(self):
        self.client.json_request = self.assert_no_retry
        self.client.delete('', retry=False)

    def test_delete_request_retry(self):
        self.client.http_request = self.assert_retry
        self.client.delete_request('', retry=True)

    def test_delete_request_no_retry(self):
        self.client.http_request = self.assert_no_retry
        self.client.delete_request('', retry=False)
