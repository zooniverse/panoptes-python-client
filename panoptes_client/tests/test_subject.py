import io
import mimetypes
import unittest
from unittest.mock import patch, mock_open, MagicMock

from panoptes_client.panoptes import ObjectNotSavedException
from panoptes_client.subject import Subject, UnknownMediaException


class TestSubject(unittest.TestCase):
    def setUp(self):
        self.subject = Subject()
        self.subject.locations = []
        self.subject._media_files = []
        self.subject.modified_attributes = set()

    def test_add_location_with_dict(self):
        location_dict = {"image/png": "https://example.com/image.png"}
        self.subject.add_location(location_dict)
        self.assertIn(location_dict, self.subject.locations)
        self.assertIn(None, self.subject._media_files)
        self.assertIn("locations", self.subject.modified_attributes)

    def test_add_location_manual_mimetype_file_like(self):
        data = b"fake image data"
        fake_file = io.BytesIO(data)
        self.subject.add_location(fake_file, manual_mimetype="image/jpeg")
        self.assertEqual(self.subject.locations[-1], "image/jpeg")
        self.assertEqual(self.subject._media_files[-1], data)
        self.assertIn("locations", self.subject.modified_attributes)

    @patch("panoptes_client.subject.magic")
    def test_add_location_magic_detection(self, mock_magic):
        mock_magic.from_buffer.return_value = "image/jpeg"
        data = b"fake image data"
        fake_file = io.BytesIO(data)
        self.subject.add_location(fake_file)
        self.assertEqual(self.subject.locations[-1], "image/jpeg")
        self.assertEqual(self.subject._media_files[-1], data)
        self.assertIn("locations", self.subject.modified_attributes)
        mock_magic.from_buffer.assert_called_with(data, mime=True)

    @patch("panoptes_client.subject.mimetypes.guess_type", return_value=("image/jpeg", None))
    def test_add_location_mimetypes_detection(self, mock_guess_type):
        import panoptes_client.subject as subject_module
        subject_module.MEDIA_TYPE_DETECTION = 'mimetypes'

        m = mock_open(read_data=b"fake image data")
        with patch("panoptes_client.subject.open", m, create=True):
            self.subject.add_location("dummy.jpg")

        self.assertEqual(self.subject.locations[-1], "image/jpeg")
        self.assertEqual(self.subject._media_files[-1], b"fake image data")
        self.assertIn("locations", self.subject.modified_attributes)

    def test_add_location_invalid_manual_mimetype(self):
        data = b"fake data"
        fake_file = io.BytesIO(data)
        with self.assertRaises(UnknownMediaException):
            self.subject.add_location(
                fake_file, manual_mimetype="application/javascript")

    def test_update_priority_requires_saved_subject(self):
        with self.assertRaises(ObjectNotSavedException):
            self.subject.update_priority(1)

    def test_update_priority_updates_priority_for_saved_subject(self):
        self.subject.id = 123
        set_member_subject_mock = MagicMock()

        with patch.object(self.subject, "save") as mock_save:
            with patch(
                "panoptes_client.subject.SetMemberSubject.where",
                return_value=iter([set_member_subject_mock]),
            ) as mock_where:
                self.subject.update_priority(
                    5,
                    subject_set_id=456,
                )

        self.assertEqual(self.subject.metadata["priority"], 5)

        mock_save.assert_called_once_with()
        mock_where.assert_called_once_with(
            subject_set_id=456,
            subject_id=123,
        )

        self.assertEqual(set_member_subject_mock.priority, 5)
        set_member_subject_mock.save.assert_called_once_with()

    def test_update_priority_updates_all_subject_sets(self):
        self.subject.id = 123

        subject_set_1 = MagicMock(id=456)
        subject_set_2 = MagicMock(id=789)
        set_member_subject_1 = MagicMock()
        set_member_subject_2 = MagicMock()

        with patch.object(self.subject, "save") as mock_save, \
            patch(
            "panoptes_client.panoptes.LinkResolver.__getattr__",
            return_value=[subject_set_1, subject_set_2],
        ),  \
            patch(
                "panoptes_client.subject.SetMemberSubject.where",
                side_effect=[
                    iter([set_member_subject_1]),
                    iter([set_member_subject_2]),
                ],
        ) as mock_where:
            self.subject.update_priority(5)

        self.assertEqual(self.subject.metadata["priority"], 5)

        mock_save.assert_called_once_with()

        self.assertEqual(mock_where.call_count, 2)
        mock_where.assert_any_call(
            subject_set_id=456,
            subject_id=123,
        )
        mock_where.assert_any_call(
            subject_set_id=789,
            subject_id=123,
        )

        self.assertEqual(set_member_subject_1.priority, 5)
        set_member_subject_1.save.assert_called_once_with()

        self.assertEqual(set_member_subject_2.priority, 5)
        set_member_subject_2.save.assert_called_once_with()
