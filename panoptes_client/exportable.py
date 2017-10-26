from __future__ import absolute_import, division, print_function

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
    """
    Abstract class containing methods for generating and downloading data
    exports.
    """

    def get_export(
        self,
        export_type,
        generate=False,
        wait=False,
        wait_timeout=None,
    ):
        """
        Downloads a data export over HTTP. Returns a file-like object
        containing the content of the export.

        - **export_type** is a string specifying which type of export should be
          downloaded.
        - **generate** is a boolean specifying whether to generate a new export
          and wait for it to be ready, or to just download the latest export.
        - **wait** is a boolean specifying whether to wait for an in-progress
          export to finish, if there is one. Has no effect if ``generate`` is
          ``True``.
        - **wait_timeout** is the number of seconds to wait if ``wait`` is
          ``True``. Has no effect if ``wait`` is ``False`` or if ``generate``
          is ``True``.

        Example::

            classification_export = Project(1234).get_export('classifications')
            for row in csv.DictReader(classification_export):
                print(row)
        """

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

    def wait_export(
        self,
        export_type,
        timeout=None,
    ):
        """
        Blocks until an in-progress export is ready.

        - **export_type** is a string specifying which type of export to wait
          for.
        - **timeout** is the maximum number of seconds to wait.

        If ``timeout`` is given and the export is not ready by the time limit,
        :py:class:`.PanoptesAPIException` is raised.
        """

        success = False
        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(
                seconds=timeout
            )

        while (not timeout) or (datetime.datetime.now() < end_time):
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
        """
        Start a new export.

        - **export_type** is a string specifying which type of export to start.

        Returns a :py:class:`dict` containing metadata for the new export.
        """

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
        """
        Fetch metadata for an export.

        - **export_type** is a string specifying which type of export to look
          up.

        Returns a :py:class:`dict` containing metadata for the export.
        """
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
