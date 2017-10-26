from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.set_member_subject import SetMemberSubject
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable


class SubjectSet(PanoptesObject):
    _api_slug = 'subject_sets'
    _link_slug = 'subject_sets'
    _edit_attributes = (
        'display_name',
        {
            'links': (
                'project',
            ),
            'metadata': (
                'category',
            )
        },
    )

    @property
    def subjects(self):
        """
        A generator which yields :py:class:`.Subject` objects which are in this
        subject set.

        Examples::

            for subject in subject_set.subjects:
                print(subject.id)

        """

        for sms in SetMemberSubject.where(subject_set_id=self.id):
            yield sms.links.subject

    @batchable
    def add(self, subjects):
        """
        Links the given subjects to this set.

        - **subjects** can be a list of :py:class:`.Subject` instances, a list
          of subject IDs, a single :py:class:`.Subject` instance, or a single
          subject ID.

        Examples::

            subject_set.add(1234)
            subject_set.add([1,2,3,4])
            subject_set.add(Subject(1234))
            subject_set.add([Subject(12), Subject(34)])
        """

        _subjects = self._build_subject_list(subjects)

        self.http_post(
            '{}/links/subjects'.format(self.id),
            json={'subjects': _subjects}
        )

    @batchable
    def remove(self, subjects):
        """
        Unlinks the given subjects from this set.

        - **subjects** can be a list of :py:class:`.Subject` instances, a list
          of subject IDs, a single :py:class:`.Subject` instance, or a single
          subject ID.

        Examples::

            subject_set.remove(1234)
            subject_set.remove([1,2,3,4])
            subject_set.remove(Subject(1234))
            subject_set.remove([Subject(12), Subject(34)])
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


LinkResolver.register(SubjectSet)
LinkResolver.register(SubjectSet, 'subject_set')
