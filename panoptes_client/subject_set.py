from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import (
    LinkCollection,
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.set_member_subject import SetMemberSubject
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable

from redo import retry


class SubjectSetLinkCollection(LinkCollection):
    def add(self, objs):
        from panoptes_client.workflow import Workflow
        if self._cls == Workflow:
            raise NotImplementedError(
                'Workflows and SubjectSets can only be linked via '
                'Workflow.links'
            )
        return super(SubjectSetLinkCollection, self).add(objs)

    def remove(self, objs):
        from panoptes_client.workflow import Workflow
        if self._cls == Workflow:
            raise NotImplementedError(
                'Workflows and SubjectSets can only be unlinked via '
                'Workflow.links'
            )
        return super(SubjectSetLinkCollection, self).remove(objs)


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
    _link_collection = SubjectSetLinkCollection

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

    def add(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.add`. Equivalent to::

            subject.links.add(subjects)
        """

        return self.links.subjects.add(subjects)

    def remove(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.remove`. Equivalent to::

            subject.links.remove(subjects)
        """

        return self.links.subjects.remove(subjects)

    def __contains__(self, subject):
        """
        Tests if the subject is linked to the subject_set.

        - **subject** a single :py:class:`.Subject` instance, or a single
          subject ID.

        Returns a boolean indicating if the subject is linked to the
        subject_set.

        Examples::
            1234 in subject_set
            Subject(1234) in subject_set
        """
        if isinstance(subject, Subject):
            _subject_id = str(subject.id)
        else:
            _subject_id = str(subject)

        linked_subject_count = SetMemberSubject.where(
            subject_set_id=self.id,
            subject_id=_subject_id
        ).object_count

        return linked_subject_count == 1


LinkResolver.register(SubjectSet)
LinkResolver.register(SubjectSet, 'subject_set')
