import io
import unittest
from unittest.mock import patch, mock_open

from panoptes_client.subject import Subject, UnknownMediaException
import mimetypes


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

    @patch.object(mimetypes, 'guess_type', return_value=("image/jpeg", None))
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
            self.subject.add_location(fake_file, manual_mimetype="application/javascript")