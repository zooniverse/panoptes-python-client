from __future__ import absolute_import, division, print_function

import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

from panoptes_client.subject_set import SubjectSet


class TestSubjectSet(unittest.TestCase):
    def test_create(self):
        with patch('panoptes_client.panoptes.Panoptes') as pc:
            pc.client().post = Mock(return_value=(
                {
                    'subject_sets': [{
                        'id': 0,
                        'display_name': '',
                    }],
                },
                '',
            ))
            subject_set = SubjectSet()
            subject_set.links.project = 1234
            subject_set.display_name = 'Name'
            subject_set.save()

            pc.client().post.assert_called_with(
                '/subject_sets',
                json={
                    'subject_sets': {
                        'display_name': 'Name',
                        'links': {
                            'project': 1234,
                        }
                    }
                },
                etag=None,
            )
