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
import mimetypes

try:
    import magic
    MEDIA_TYPE_DETECTION = 'magic'
except ImportError:
    import importlib.metadata
    try:
        importlib.metadata.version("python-magic")
        logging.getLogger('panoptes_client').info(
            'libmagic not operational, likely due to lack of shared libraries. '
            'Media MIME type determination will be based on file extensions.'
        )
    except importlib.metadata.PackageNotFoundError:
        pass
    MEDIA_TYPE_DETECTION = 'mimetypes'

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

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "audio/mpeg",
    "video/mp4",
    "audio/mp4",
    "video/mpeg",
    "text/plain",
    "application/json",
]

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
        Returns a context manager to allow asynchronously creating subjects or creating subject attached images
        .
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

            with Subject.async_saves():
                local_files = [...]
                for filename in local_files:
                    s = Subject(1234)
                    s.save_attached_image(local_file)

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

    def _detect_media_type(self, media_data=None, manual_mimetype=None):
        if manual_mimetype is not None:
            return manual_mimetype

        if MEDIA_TYPE_DETECTION == 'magic':
            return magic.from_buffer(media_data, mime=True)

        media_type = mimetypes.guess_type(media_data)[0]
        if not media_type:
            raise UnknownMediaException(
                'Could not detect file type. Please try installing '
                'libmagic: https://panoptes-python-client.readthedocs.'
                'io/en/latest/user_guide.html#uploading-non-image-'
                'media-types'
            )
        return media_type

    def _validate_media_type(self, media_type=None):
        if media_type not in ALLOWED_MIME_TYPES:
            raise UnknownMediaException(f"File type {media_type} is not allowed.")

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

    @property
    def attached_images(self):
        return self.http_get('{}/attached_images'.format(self.id))[0]

    def set_raw(self, raw, etag=None, loaded=True):
        super(Subject, self).set_raw(raw, etag, loaded)
        if loaded and self.metadata:
            self._original_metadata = deepcopy(self.metadata)

    def subject_workflow_status(self, workflow_id):
        """
        Returns SubjectWorkflowStatus of Subject in Workflow

        Example::

            subject.subject_workflow_status(4321)
        """
        return next(SubjectWorkflowStatus.where(subject_id=self.id, workflow_id=workflow_id))

    def add_location(self, location, manual_mimetype=None):
        """
        Add a media location to this subject.

        - **location** can be an open :py:class:`file` object, a path to a
          local file, or a :py:class:`dict` containing MIME types and URLs for
          remote media.

        - **manual_mimetype** optional, passes in a specific MIME type for media item.

        Examples::

            subject.add_location(my_file)
            subject.add_location('/data/image.jpg')
            subject.add_location({'image/png': 'https://example.com/image.png'})
            subject.add_location(my_file, manual_mimetype='image/png')
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
            media_type = self._detect_media_type(media_data, manual_mimetype)

            self._validate_media_type(media_type)

            self.locations.append(media_type)
            self._media_files.append(media_data)
            self.modified_attributes.add('locations')
        finally:
            f.close()

    def add_attached_image(
        self,
        src=None,
        content_type='image/png',
        external_link=True,
        metadata=None,
        client=None
    ):
        metadata = metadata or {}
        media_data = {
            'content_type': content_type,
            'external_link': external_link,
            'metadata': metadata,
        }
        if src:
            media_data['src'] = src

        if not client:
            client = Panoptes.client()

        with client:
            json_response, _ = self.http_post('{}/attached_images'.format(self.id), json={'media': media_data})

            return json_response['media'][0]['src']

    def _save_attached_image(self, attached_media, manual_mimetype=None, metadata=None, client=None):
        if not client:
            client = Panoptes.client()

        with client:
            metadata = metadata or {}

            if type(attached_media) is dict:
                for content_type, url in attached_media.items():
                    self.add_attached_image(
                        src=url,
                        content_type=content_type,
                        metadata=metadata,
                        external_link=True,
                    )
                return
            elif type(attached_media) in (str,) + _OLD_STR_TYPES:
                f = open(attached_media, 'rb')
            else:
                f = attached_media

            media_type = None
            try:
                media_data = f.read()
                media_type = self._detect_media_type(media_data, manual_mimetype)
                self._validate_media_type(media_type)
            finally:
                f.close()
            file_url = self.add_attached_image(
                src=None,
                content_type=media_type,
                metadata=metadata,
                external_link=False,
            )
            self._upload_media(file_url, media_data, media_type)

    def save_attached_image(self, attached_media, manual_mimetype=None, metadata=None, client=None):
        """
        Add a attached_media to this subject.
        NOTE: This should NOT be confused with subject location.
        A subject location is the content of the subject that a volunteer will classify.
        A subject attached_media is ancillary data associated to the subject that get displayed on the Subject's Talk Page.

        - **attached_media** can be an open :py:class:`file` object, a path to a
          local file, or a :py:class:`dict` containing MIME types and URLs for
          remote media.
        - **metadata** can be a :py:class:`dict` that stores additional info on attached_media.

        Examples::

            subject.save_attached_image(my_file)
            subject.save_attached_image('/data/image.jpg')
            subject.save_attached_image(my_file, {'metadata_test': 'Object 1'})
        """
        if not client:
            client = Panoptes.client()

        async_save = hasattr(self._local, 'save_exec')

        future_result = None
        with client:
            metadata = metadata or {}

            try:
                if async_save:
                    upload_exec = self._local.save_exec
                else:
                    upload_exec = ThreadPoolExecutor(max_workers=ASYNC_SAVE_THREADS)
                future_result = upload_exec.submit(
                    retry,
                    self._save_attached_image,
                    args=(
                        attached_media,
                        manual_mimetype,
                        metadata,
                        client
                    ),
                    attempts=UPLOAD_RETRY_LIMIT,
                    sleeptime=RETRY_BACKOFF_INTERVAL,
                    retry_exceptions=(
                        requests.exceptions.RequestException
                    ),
                    log_args=False,
                )
            finally:
                if not async_save:
                    # Shuts down and waits for the task if this isn't being used in a `async_saves` block
                    upload_exec.shutdown(wait=True)
        return future_result


class UnknownMediaException(Exception):
    pass


LinkResolver.register(Subject)
LinkResolver.register(Subject, 'subject')
