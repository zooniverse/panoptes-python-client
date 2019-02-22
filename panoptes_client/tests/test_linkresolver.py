from __future__ import absolute_import, division, print_function

import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import Mock
else:
    from unittest.mock import Mock

from panoptes_client.panoptes import LinkResolver


class TestLinkResolver(unittest.TestCase):
    def test_set_new_link(self):
        parent = Mock()
        parent.raw = {'links': {}}

        target = Mock()

        resolver = LinkResolver(parent)
        resolver.newlink = target
        self.assertEqual(parent.raw['links'].get('newlink', None), target)
