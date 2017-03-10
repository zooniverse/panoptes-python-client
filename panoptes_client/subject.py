import imghdr
import requests
import time

from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.utils import batchable

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
        self._image_files = []

    def save(self):
        response = super(Subject, self).save()
        for location, image_file in zip(
            response['subjects'][0]['locations'],
            self._image_files
        ):
            if not image_file:
                continue

            try:
                for image_type, url in location.items():
                    image_data = image_file.read()
                    for attempt in range(UPLOAD_RETRY_LIMIT):
                        try:
                            upload_response = requests.put(
                                url,
                                headers={
                                    'Content-Type': image_type,
                                },
                                data=image_data,
                            )
                            upload_response.raise_for_status()
                            break
                        except requests.exceptions.RequestException:
                            if (attempt + 1) >= UPLOAD_RETRY_LIMIT:
                                raise
                            else:
                                time.sleep(attempt * RETRY_BACKOFF_INTERVAL)
            finally:
                image_file.close()

    def add_location(self, location):
        if type(location) is dict:
            self.locations.append(location)
            self._image_files.append(None)
            return
        elif type(location) in (str, unicode):
            f = open(location, 'rb')
        else:
            f = location

        image_type = imghdr.what(f)
        self.locations.append(
            'image/{}'.format(image_type)
        )
        self._image_files.append(f)

LinkResolver.register(Subject)
LinkResolver.register(Subject, 'subject')
