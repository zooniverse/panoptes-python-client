import io
import os
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import Mock, patch

from panoptes_client.subject import Subject, UnknownMediaException


class TestMediaTypeFallback(unittest.TestCase):
    def setUp(self):
        self.detection = patch(
            'panoptes_client.subject.MEDIA_TYPE_DETECTION', 'mimetypes',
        )
        self.detection.start()
        self.addCleanup(self.detection.stop)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.data = b'\x89PNG\r\n\x1a\n'
        self.subject = Subject()

    def make_file(self, name):
        path = os.path.join(self.directory.name, name)
        with open(path, 'wb') as file:
            file.write(self.data)
        return path

    def test_local_paths_use_extension_instead_of_binary_content(self):
        for name, media_type in (
            ('image.png', 'image/png'),
            ('image.jpg', 'image/jpeg'),
            ('video.mp4', 'video/mp4'),
        ):
            with self.subTest(name=name):
                self.subject.add_location(self.make_file(name))
                self.assertEqual(self.subject.locations[-1], media_type)
                self.assertEqual(self.subject._media_files[-1], self.data)
        self.assertIn('locations', self.subject.modified_attributes)

    def test_open_file_uses_its_name(self):
        file = open(self.make_file('image.png'), 'rb')
        self.subject.add_location(file)
        self.assertEqual(self.subject.locations, ['image/png'])
        self.assertTrue(file.closed)

    def test_named_buffer_uses_its_name(self):
        file = io.BytesIO(self.data)
        file.name = 'image.png'
        self.subject.add_location(file)
        self.assertEqual(self.subject.locations, ['image/png'])

    def test_unnamed_buffer_has_actionable_error(self):
        file = io.BytesIO(self.data)
        with self.assertRaisesRegex(UnknownMediaException, 'manual_mimetype'):
            self.subject.add_location(file)
        self.assertTrue(file.closed)
        self.assertEqual(self.subject.locations, [])

    def test_unnamed_buffer_with_override_still_works(self):
        self.subject.add_location(
            io.BytesIO(self.data), manual_mimetype='image/png',
        )
        self.assertEqual(self.subject.locations, ['image/png'])

    def test_unknown_extension_has_actionable_error(self):
        with self.assertRaisesRegex(UnknownMediaException, 'manual_mimetype'):
            self.subject.add_location(self.make_file('image.unknownextension'))

    def test_magic_still_uses_content(self):
        magic = Mock()
        magic.from_buffer.return_value = 'image/png'
        with patch('panoptes_client.subject.MEDIA_TYPE_DETECTION', 'magic'):
            with patch('panoptes_client.subject.magic', magic, create=True):
                self.subject.add_location(io.BytesIO(self.data))
        magic.from_buffer.assert_called_once_with(self.data, mime=True)
        self.assertEqual(self.subject.locations, ['image/png'])

    def test_attached_media_uses_filename(self):
        path = self.make_file('image.png')
        with patch.object(self.subject, '_add_attached_image') as add_image:
            with patch.object(self.subject, '_upload_media') as upload:
                add_image.return_value = 'https://example.com/upload'
                self.subject._save_attached_image(path, client=nullcontext())
        add_image.assert_called_once_with(
            src=None, content_type='image/png', metadata={},
            external_link=False,
        )
        upload.assert_called_once_with(
            'https://example.com/upload', self.data, 'image/png',
        )
