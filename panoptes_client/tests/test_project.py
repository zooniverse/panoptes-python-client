from __future__ import absolute_import, division, print_function

import unittest

from panoptes_client import Project
from panoptes_client.panoptes import PanoptesAPIException


class TestProject(unittest.TestCase):
    def test_find_id(self):
        p = Project.find(1)
        self.assertEqual(p.id, '1')

    def test_find_slug(self):
        p = Project.find(slug='zooniverse/snapshot-supernova')
        self.assertEqual(p.id, '1')

    def test_find_unknown_id(self):
        p = Project.find(0)
        self.assertEqual(p, None)

    def test_find_unknown_slug(self):
        with self.assertRaises(PanoptesAPIException):
            Project.find(slug='invalid_slug')
