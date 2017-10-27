from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import PanoptesObject
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable


class Collection(PanoptesObject):
    _api_slug = 'collections'
    _link_slug = 'collections'
    _edit_attributes = (
        'name',
        'display_name',
        'private'
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
