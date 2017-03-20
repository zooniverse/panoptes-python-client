import datetime
import time

import requests

from panoptes_client.panoptes import (
    PanoptesAPIException,
    Talk,
)


TALK_EXPORT_TYPES = (
    'talk_comments',
    'talk_tags',
)

talk = Talk()


class Exportable(object):
    def get_export(
        self,
        export_type,
        generate=False,
        wait=False,
        wait_timeout=60,
    ):

        if generate:
            self.generate_export(export_type)

        if generate or wait:
            export = self.wait_export(export_type, wait_timeout)
        else:
            export = self.describe_export(export_type)

        if export_type in TALK_EXPORT_TYPES:
            media_url = export['data_requests'][0]['url']
        else:
            media_url = export['media'][0]['src']

        return requests.get(media_url, stream=True)

    def wait_export(self, export_type, timeout=60):
        success = False
        end_time = datetime.datetime.now() + datetime.timedelta(
            seconds=timeout
        )

        while datetime.datetime.now() < end_time:
            export_description = self.describe_export(
                export_type,
            )

            if export_type in TALK_EXPORT_TYPES:
                export_metadata = export_description['data_requests'][0]
            else:
                export_metadata = export_description['media'][0]['metadata']

            if export_metadata.get('state', '') in ('ready', 'finished'):
                success = True
                break

            time.sleep(2)

        if not success:
            raise PanoptesAPIException(
                '{}_export not ready within {} seconds'.format(
                    export_type,
                    timeout
                )
            )

        return export_description

    def generate_export(self, export_type):
        if export_type in TALK_EXPORT_TYPES:
            return talk.post_data_request(
                'project-{}'.format(self.id),
                export_type.replace('talk_', '')
            )

        return self.http_post(
            self._export_path(export_type),
            json={"media": {"content_type": "text/csv"}},
        )[0]

    def describe_export(self, export_type):
        if export_type in TALK_EXPORT_TYPES:
            return talk.get_data_request(
                'project-{}'.format(self.id),
                export_type.replace('talk_', '')
            )[0]

        return self.http_get(
            self._export_path(export_type),
        )[0]

    def _export_path(self, export_type):
        return '{}/{}_export'.format(self.id, export_type)
