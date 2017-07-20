
from panoptes_client.panoptes import Panoptes

import datetime
import unittest
from unittest.mock import patch


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

        print(datetime.datetime.now())

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.bearer_expired() is False

    def test_early_2(self):
        target = datetime.datetime(2017, 1, 1, 11, 58, 0)
        MockDate.fake(target)

        print(datetime.datetime.now())

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.bearer_expired() is False

    def test_late(self):
        target = datetime.datetime(2017, 1, 1, 14, 0, 0)
        MockDate.fake(target)

        print(datetime.datetime.now())

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.bearer_expired() is True

    def test_late_2(self):
        target = datetime.datetime(2017, 1, 1, 12, 0, 1)
        MockDate.fake(target)

        print(datetime.datetime.now())

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.bearer_expired() is True

    def test_in_buffer(self):
        target = datetime.datetime(2017, 1, 1, 11, 59, 0)
        MockDate.fake(target)

        print(datetime.datetime.now())

        client = Panoptes()
        client.bearer_token = True

        client.bearer_expires = datetime.datetime(2017, 1, 1, 12, 0, 0)

        assert client.bearer_expired() is True
