from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import (
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable


class Collection(PanoptesObject):
    _api_slug = 'collections'
    _link_slug = 'collections'
    _edit_attributes = (
        'name',
        'description',
        'display_name',
        'private',
        {
            'links': (
                'project',
            ),
        },
    )

    @classmethod
    def find(cls, id='', slug=None):
        """
        Similar to :py:meth:`.PanoptesObject.find`, but allows lookup by slug
        as well as ID.

        Examples::

            collection_1234 = Collection.find(1234)
            my_collection = Collection.find(slug="example/my-collection")
        """

        if not id and not slug:
            return None
        try:
            return cls.where(id=id, slug=slug).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find collection with slug='{}'".format(slug)
            )

    @property
    def subjects(self):
        """
        A generator which yields each :py:class:`.Subject` in this collection.
        """

        return Subject.where(collection_id=self.id)

    @batchable
    def add(self, subjects):
        """
        Links the given subjects to this collection.

        - **subjects** can be a list of :py:class:`.Subject` instances, a list
          of subject IDs, a single :py:class:`.Subject` instance, or a single
          subject ID.

        Examples::

            collection.add(1234)
            collection.add([1,2,3,4])
            collection.add(Subject(1234))
            collection.add([Subject(12), Subject(34)])
        """
        _subjects = self._build_subject_list(subjects)

        self.http_post(
            '{}/links/subjects'.format(self.id),
            json={'subjects': _subjects}
        )

    @batchable
    def remove(self, subjects):
        """
        Unlinks the given subjects from this collection.

        - **subjects** can be a list of :py:class:`.Subject` instances, a list
          of subject IDs, a single :py:class:`.Subject` instance, or a single
          subject ID.

        Examples::

            collection.remove(1234)
            collection.remove([1,2,3,4])
            collection.remove(Subject(1234))
            collection.remove([Subject(12), Subject(34)])
        """
        _subjects = self._build_subject_list(subjects)

        _subjects_ids = ",".join(_subjects)
        self.http_delete(
            '{}/links/subjects/{}'.format(self.id, _subjects_ids)
        )

    def _build_subject_list(self, subjects):
        _subjects = []
        for subject in subjects:
            if not (
                isinstance(subject, Subject)
                or isinstance(subject, (int, str,))
            ):
                raise TypeError

            if isinstance(subject, Subject):
                _subject_id = subject.id
            else:
                _subject_id = str(subject)

            _subjects.append(_subject_id)

        return _subjects

    def set_default_subject(self, subject):
        """
        Sets the subject's location media URL as a link.
        It displays as the default subject on PFE.

        - **subject** can be a single :py:class:`.Subject` instance or a single
          subject ID.

        Examples::

            collection.set_default_subject(1234)
            collection.set_default_subject(Subject(1234))
        """
        if not (
            isinstance(subject, Subject)
            or isinstance(subject, (int, str,))
        ):
            raise TypeError
        if isinstance(subject, Subject):
            _subject_id = subject.id
        else:
            _subject_id = str(subject)

        self.http_post(
            '{}/links/default_subject'.format(self.id),
            json={'default_subject': _subject_id},
        )


LinkResolver.register(Collection)
