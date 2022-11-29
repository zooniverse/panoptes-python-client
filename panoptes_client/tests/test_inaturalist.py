from __future__ import absolute_import, division, print_function

import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

from panoptes_client.inaturalist import Inaturalist


class TestInaturalist(unittest.TestCase):

    def test_inat_import(self):
        with patch('panoptes_client.panoptes.Panoptes.client') as pc:
            pc().post = Mock(return_value=200)
            Inaturalist.inat_import(16462, 4)

            pc().post.assert_called_with(
                '/inaturalist/import',
                json={
                    'taxon_id': 16462,
                    'subject_set_id': 4,
                    'updated_since': None
                }
            )

    def test_inat_import_updated_since(self):
        with patch('panoptes_client.panoptes.Panoptes.client') as pc:
            pc().post = Mock(return_value=200)
            Inaturalist.inat_import(16462, 4, '2022-10-31')

            pc().post.assert_called_with(
                '/inaturalist/import',
                json={
                    'taxon_id': 16462,
                    'subject_set_id': 4,
                    'updated_since': '2022-10-31'
                }
            )
