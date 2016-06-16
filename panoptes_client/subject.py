import imghdr
import requests

from panoptes_client.panoptes import PanoptesObject, LinkResolver

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

            for image_type, url in location.items():
                upload_response = requests.put(
                    url,
                    headers={
                        'Content-Type': image_type,
                    },
                    data=image_file.read(),
                )
                upload_response.raise_for_status()

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
