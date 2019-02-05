from __future__ import absolute_import, division, print_function
from builtins import str

import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import Mock, patch
else:
    from unittest.mock import Mock, patch

from panoptes_client.panoptes import LinkCollection, ObjectNotSavedException


LINKED_OBJECT_IDS = ('1', '2', '3', '4')


class MockPanoptesObject(Mock):
    def __init__(self, raw=None, etag=None):
        r = super(MockPanoptesObject, self).__init__()
        self.id = str(raw)
        return r


class TestLinkCollection(unittest.TestCase):
    def link_collection(self, ids=LINKED_OBJECT_IDS, parent=None):
        if parent:
            mock_parent = parent
        else:
            mock_parent = Mock()

        mock_slug = Mock()
        lc = LinkCollection(
            cls=MockPanoptesObject,
            slug=mock_slug,
            parent=mock_parent,
            linked_objects=[str(_id) for _id in ids],
        )
        return lc, mock_parent, mock_slug

    def test_contains_id_int(self):
        self.assertTrue(1 in self.link_collection()[0])

    def test_contains_id_str(self):
        self.assertTrue('1' in self.link_collection()[0])

    def test_contains_obj(self):
        mock_obj = MockPanoptesObject(1)
        self.assertTrue(mock_obj in self.link_collection()[0])

    def test_not_contains_id_int(self):
        self.assertFalse(9 in self.link_collection()[0])

    def test_not_contains_id_str(self):
        self.assertFalse('9' in self.link_collection()[0])

    def test_not_contains_obj(self):
        mock_obj = MockPanoptesObject(9)
        self.assertFalse(mock_obj in self.link_collection()[0])

    def test_getitem_exists(self):
        lc = self.link_collection()[0]
        for i, _id in zip(range(len(LINKED_OBJECT_IDS)), LINKED_OBJECT_IDS):
            self.assertEqual(lc[i].id, _id)

    def test_getitem_doesnt_exist(self):
        with self.assertRaises(IndexError):
            self.link_collection()[0][len(LINKED_OBJECT_IDS)]

    def test_iter_empty(self):
        m = Mock()
        for _ in self.link_collection([])[0]:
            m()
        m.assert_not_called()

    def test_iter_full(self):
        m = Mock()
        for _ in self.link_collection()[0]:
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS))

    def test_add_empty_noop(self):
        m = Mock()
        lc, parent, slug = self.link_collection([])
        lc.add([])
        parent.http_post.assert_not_called()
        for _ in lc:
            m()
        m.assert_not_called()

    def test_add_id_single(self):
        lc, parent, slug = self.link_collection([])
        lc.add(1)
        parent.http_post.assert_called_with(
            '{}/links/{}'.format(parent.id, slug),
            json={slug: ['1']},
            retry=True,
        )
        m = Mock()
        for obj in lc:
            self.assertEqual(obj.id, '1')
            m()
        self.assertEqual(m.call_count, 1)

    def test_add_id_list(self):
        lc, parent, slug = self.link_collection([])
        lc.add(LINKED_OBJECT_IDS)
        parent.http_post.assert_called_with(
            '{}/links/{}'.format(parent.id, slug),
            json={slug: list(LINKED_OBJECT_IDS)},
            retry=True,
        )
        m = Mock()
        for obj, _id in zip(lc, LINKED_OBJECT_IDS):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS))

    def test_add_object_single(self):
        lc, parent, slug = self.link_collection([])
        lc.add(MockPanoptesObject(1))
        parent.http_post.assert_called_with(
            '{}/links/{}'.format(parent.id, slug),
            json={slug: ['1']},
            retry=True,
        )
        m = Mock()
        for obj in lc:
            self.assertEqual(obj.id, '1')
            m()
        self.assertEqual(m.call_count, 1)

    def test_add_object_list(self):
        lc, parent, slug = self.link_collection([])
        lc.add([MockPanoptesObject(_id) for _id in LINKED_OBJECT_IDS])
        parent.http_post.assert_called_with(
            '{}/links/{}'.format(parent.id, slug),
            json={slug: list(LINKED_OBJECT_IDS)},
            retry=True,
        )
        m = Mock()
        for obj, _id in zip(lc, LINKED_OBJECT_IDS):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS))

    def test_add_readonly(self):
        with patch('panoptes_client.panoptes.LinkResolver') as lr:
            lr.isreadonly = lambda s: True
            lc = self.link_collection()[0]
            with self.assertRaises(NotImplementedError):
                lc.add(1)

    def test_add_not_saved(self):
        parent = MockPanoptesObject()
        parent.id = None
        lc = self.link_collection(parent=parent)[0]
        with self.assertRaises(ObjectNotSavedException):
            lc.add(1)

    def test_remove_empty_noop(self):
        m = Mock()
        lc, parent, slug = self.link_collection()
        lc.remove([])
        parent.http_delete.assert_not_called()
        for obj, _id in zip(lc, LINKED_OBJECT_IDS):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS))

    def test_remove_id_single(self):
        m = Mock()
        lc, parent, slug = self.link_collection()
        lc.remove(LINKED_OBJECT_IDS[0])
        parent.http_delete.assert_called_with(
            '{}/links/{}/1'.format(parent.id, slug),
            retry=True,
        )
        for obj, _id in zip(lc, LINKED_OBJECT_IDS[1:]):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS) - 1)

    def test_remove_id_list(self):
        m = Mock()
        removed_ids = LINKED_OBJECT_IDS[:-1]
        lc, parent, slug = self.link_collection()
        lc.remove(removed_ids)
        parent.http_delete.assert_called_with(
            '{}/links/{}/{}'.format(
                parent.id,
                slug,
                ",".join(removed_ids),
            ),
            retry=True,
        )
        for obj, _id in zip(lc, LINKED_OBJECT_IDS[-1:]):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, 1)

    def test_remove_object_single(self):
        m = Mock()
        lc, parent, slug = self.link_collection()
        lc.remove(MockPanoptesObject(LINKED_OBJECT_IDS[0]))
        parent.http_delete.assert_called_with(
            '{}/links/{}/1'.format(parent.id, slug),
            retry=True,
        )
        for obj, _id in zip(lc, LINKED_OBJECT_IDS[1:]):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, len(LINKED_OBJECT_IDS) - 1)

    def test_remove_object_list(self):
        m = Mock()
        removed_ids = LINKED_OBJECT_IDS[:-1]
        lc, parent, slug = self.link_collection()
        lc.remove([MockPanoptesObject(_id) for _id in removed_ids])
        parent.http_delete.assert_called_with(
            '{}/links/{}/{}'.format(
                parent.id,
                slug,
                ",".join(removed_ids),
            ),
            retry=True,
        )
        for obj, _id in zip(lc, LINKED_OBJECT_IDS[-1:]):
            self.assertEqual(obj.id, _id)
            m()
        self.assertEqual(m.call_count, 1)

    def test_remove_readonly(self):
        with patch('panoptes_client.panoptes.LinkResolver') as lr:
            lr.isreadonly = lambda s: True
            lc = self.link_collection()[0]
            with self.assertRaises(NotImplementedError):
                lc.remove(1)

    def test_remove_not_saved(self):
        parent = MockPanoptesObject()
        parent.id = None
        lc = self.link_collection(parent=parent)[0]
        with self.assertRaises(ObjectNotSavedException):
            lc.remove(1)
