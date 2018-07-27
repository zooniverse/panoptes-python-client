from __future__ import absolute_import, division, print_function

_OLD_STR_TYPES = (str,)
try:
    _OLD_STR_TYPES = _OLD_STR_TYPES + (unicode,)
except NameError:
    pass

from builtins import range, str

import requests
import time

try:
    import magic
    MEDIA_TYPE_DETECTION = 'magic'
except ImportError:
    import imghdr
    MEDIA_TYPE_DETECTION = 'imghdr'

from panoptes_client.panoptes import PanoptesObject, LinkResolver

UPLOAD_RETRY_LIMIT = 5
RETRY_BACKOFF_INTERVAL = 5

class Subject(PanoptesObject):
    _api_slug = 'subjects'
    _link_slug = 'subjects'
    _edit_attributes = (
        'locations',
        'metadata',
        {
            'links': (
                'project',
            ),
        },
    )

    def __init__(self, raw={}, etag=None):
        super(Subject, self).__init__(raw, etag)
        if not self.locations:
            self.locations = []
        if not self.metadata:
            self.metadata = {}
            self._original_metadata = {}
        self._media_files = []

    def save(self):
        """
        Like :py:meth:`.PanoptesObject.save`, but also uploads any local files
        which have previosly been added to the subject with
        :py:meth:`add_location`. Automatically retries uploads on error.
        """
        if not self.metadata == self._original_metadata:
            self.modified_attributes.add('metadata')

        response = super(Subject, self).save()

        if not response:
            return

        for location, media_data in zip(
            response['subjects'][0]['locations'],
            self._media_files
        ):
            if not media_data:
                continue

            for media_type, url in location.items():
                for attempt in range(UPLOAD_RETRY_LIMIT):
                    try:
                        upload_response = requests.put(
                            url,
                            headers={
                                'Content-Type': media_type,
                            },
                            data=media_data,
                        )
                        upload_response.raise_for_status()
                        break
                    except requests.exceptions.RequestException:
                        if (attempt + 1) >= UPLOAD_RETRY_LIMIT:
                            raise
                        else:
                            time.sleep(attempt * RETRY_BACKOFF_INTERVAL)

    def set_raw(self, raw, etag=None, loaded=True):
        super(Subject, self).set_raw(raw, etag, loaded)
        if loaded and self.metadata:
            self._original_metadata = dict(self.metadata)
        elif loaded:
            self._original_metadata = None

    def add_location(self, location):
        """
        Add a media location to this subject.

        - **location** can be an open :py:class:`file` object, a path to a
          local file, or a :py:class:`dict` containing MIME types and URLs for
          remote media.

        Examples::

            subject.add_location(my_file)
            subject.add_location('/data/image.jpg')
            subject.add_location({'image/png': 'https://example.com/image.png'})
        """
        if type(location) is dict:
            self.locations.append(location)
            self._media_files.append(None)
            return
        elif type(location) in (str,) + _OLD_STR_TYPES:
            f = open(location, 'rb')
        else:
            f = location

        try:
            media_data = f.read()
            if MEDIA_TYPE_DETECTION == 'magic':
                media_type = magic.from_buffer(media_data, mime=True)
            else:
                media_type = 'image/{}'.format(imghdr.what(None, media_data))
            self.locations.append(media_type)
            self._media_files.append(media_data)
        finally:
            f.close()

LinkResolver.register(Subject)
LinkResolver.register(Subject, 'subject')
