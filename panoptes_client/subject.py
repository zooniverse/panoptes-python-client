from __future__ import absolute_import, division, print_function
from panoptes_client.subject_workflow_status import SubjectWorkflowStatus

_OLD_STR_TYPES = (str,)
try:
    _OLD_STR_TYPES = _OLD_STR_TYPES + (unicode,)
except NameError:
    pass

from builtins import range, str

import logging
import requests
import threading
import time

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

try:
    import magic
    MEDIA_TYPE_DETECTION = 'magic'
except ImportError:
    import pkg_resources
    try:
        pkg_resources.require("python-magic")
        logging.getLogger('panoptes_client').warn(
            'Broken libmagic installation detected. The python-magic module is'
            ' installed but can\'t be imported. Please check that both '
            'python-magic and the libmagic shared library are installed '
            'correctly. Uploading media other than images may not work.'
        )
    except pkg_resources.DistributionNotFound:
        pass
    import imghdr
    MEDIA_TYPE_DETECTION = 'imghdr'

from panoptes_client.panoptes import (
    LinkResolver,
    Panoptes,
    PanoptesAPIException,
    PanoptesObject,
)
from redo import retry

UPLOAD_RETRY_LIMIT = 5
RETRY_BACKOFF_INTERVAL = 5
ASYNC_SAVE_THREADS = 5

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
    _local = threading.local()

    @classmethod
    def async_saves(cls):
        """
        Returns a context manager to allow asynchronously creating subjects.
        Using this context manager will create a pool of threads which will
        create multiple subjects at once and upload any local files
        simultaneously.

        The recommended way to use this is with the `with` statement::

            with Subject.async_saves():
                local_files = [...]
                for filename in local_files:
                    s = Subject()
                    s.links.project = 1234
                    s.add_location(filename)
                    s.save()

        Alternatively, you can manually shut down the thread pool::

            pool = Subject.async_saves()
            local_files = [...]
            try:
                for filename in local_files:
                    s = Subject()
                    s.links.project = 1234
                    s.add_location(filename)
                    s.save()
            finally:
                pool.shutdown()
        """
        cls._local.save_exec = ThreadPoolExecutor(
            max_workers=ASYNC_SAVE_THREADS
        )
        return cls._local.save_exec

    def __init__(self, raw={}, etag=None):
        super(Subject, self).__init__(raw, etag)
        if not self.locations:
            self.locations = []
        if not self.metadata:
            self.metadata = {}
            self._original_metadata = {}
        self._media_files = [None] * len(self.locations)

    def save(self, client=None):
        """
        Like :py:meth:`.PanoptesObject.save`, but also uploads any local files
        which have previosly been added to the subject with
        :py:meth:`add_location`. Automatically retries uploads on error.

        If multiple local files are to be uploaded, several files will be
        uploaded simultaneously to save time.
        """
        if not client:
            client = Panoptes.client()

        async_save = hasattr(self._local, 'save_exec')

        with client:
            if async_save:
                try:
                    # The recursive call will exec in a new thread, so
                    # self._local.save_exec will be undefined above
                    self._async_future = self._local.save_exec.submit(
                        self.save,
                        client=client,
                    )
                    return
                except RuntimeError:
                    del self._local.save_exec
                    async_save = False

            if not self.metadata == self._original_metadata:
                self.modified_attributes.add('metadata')

            response = retry(
                super(Subject, self).save,
                attempts=UPLOAD_RETRY_LIMIT,
                sleeptime=RETRY_BACKOFF_INTERVAL,
                retry_exceptions=(PanoptesAPIException,),
                log_args=False,
            )

            if not response:
                return

            try:
                if async_save:
                    upload_exec = self._local.save_exec
                else:
                    upload_exec = ThreadPoolExecutor(
                        max_workers=ASYNC_SAVE_THREADS,
                    )

                for location, media_data in zip(
                    response['subjects'][0]['locations'],
                    self._media_files
                ):
                    if not media_data:
                        continue

                    for media_type, url in location.items():
                        upload_exec.submit(
                            retry,
                            self._upload_media,
                            args=(url, media_data, media_type),
                            attempts=UPLOAD_RETRY_LIMIT,
                            sleeptime=RETRY_BACKOFF_INTERVAL,
                            retry_exceptions=(
                                requests.exceptions.RequestException,
                            ),
                            log_args=False,
                        )

                self._media_files = [None] * len(self.locations)

            finally:
                if not async_save:
                    upload_exec.shutdown()

    def _upload_media(self, url, media_data, media_type):
        upload_response = requests.put(
            url,
            headers={
                'Content-Type': media_type,
                'x-ms-blob-type': 'BlockBlob',
            },
            data=media_data,
        )
        upload_response.raise_for_status()
        return upload_response

    @property
    def async_save_result(self):
        """
        Retrieves the result of this subject's asynchronous save.

        - Returns `True` if the subject was saved successfully.
        - Raises `concurrent.futures.CancelledError` if the save was cancelled.
        - If the save failed, raises the relevant exception.
        - Returns `False` if the subject hasn't finished saving or if the
          subject has not been queued for asynchronous save.
        """
        if hasattr(self, "_async_future") and self._async_future.done():
            self._async_future.result()
            return True
        else:
            return False

    def set_raw(self, raw, etag=None, loaded=True):
        super(Subject, self).set_raw(raw, etag, loaded)
        if loaded and self.metadata:
            self._original_metadata = deepcopy(self.metadata)
        elif loaded:
            self._original_metadata = None

    def subject_workflow_status(self, workflow_id):
        """
        Returns SubjectWorkflowStatus of Subject in Workflow

        Example::

            subject.subject_workflow_status(4321)
        """
        return next(SubjectWorkflowStatus.where(subject_id=self.id, workflow_id=workflow_id))

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
            self.modified_attributes.add('locations')
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
                media_type = imghdr.what(None, media_data)
                if not media_type:
                    raise UnknownMediaException(
                        'Could not detect file type. Please try installing '
                        'libmagic: https://panoptes-python-client.readthedocs.'
                        'io/en/latest/user_guide.html#uploading-non-image-'
                        'media-types'
                    )
                media_type = 'image/{}'.format(media_type)
            self.locations.append(media_type)
            self._media_files.append(media_data)
            self.modified_attributes.add('locations')
        finally:
            f.close()


class UnknownMediaException(Exception):
    pass


LinkResolver.register(Subject)
LinkResolver.register(Subject, 'subject')
