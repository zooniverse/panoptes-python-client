from __future__ import absolute_import, division, print_function
from builtins import str
from panoptes_client.subject_workflow_status import SubjectWorkflowStatus

from panoptes_client.panoptes import (
    LinkCollection,
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.set_member_subject import SetMemberSubject
from panoptes_client.subject import Subject
from panoptes_client.exportable import Exportable
from panoptes_client.utils import batchable

from redo import retry


class SubjectSetLinkCollection(LinkCollection):
    def __contains__(self, obj):
        if self._cls == Subject:
            if isinstance(obj, Subject):
                _subject_id = str(obj.id)
            else:
                _subject_id = str(obj)

            linked_subject_count = SetMemberSubject.where(
                subject_set_id=self._parent.id,
                subject_id=_subject_id
            ).object_count

            return linked_subject_count == 1
        return super(SubjectSetLinkCollection, self).__contains__(obj)

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


class SubjectSet(PanoptesObject, Exportable):
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

    def set_raw(self, raw, etag=None, loaded=True):
        raw.setdefault('links', {}).setdefault('subjects', [])
        return super(SubjectSet, self).set_raw(raw, etag, loaded)

    def add(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.add`. Equivalent to::

            subject_set.links.add(subjects)
        """

        return self.links.subjects.add(subjects)

    def remove(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.remove`. Equivalent to::

            subject_set.links.remove(subjects)
        """

        return self.links.subjects.remove(subjects)

    def subject_workflow_statuses(self, workflow_id):
        """
        A generator which yields :py:class:`.SubjectWorkflowStatus` objects for subjects in this
        subject set and for the supplied workflow id.

        Examples::

            for status in subject_set.subject_workflow_statuses(1234):
                print(status.retirement_reason)
        """

        subject_ids = ', '.join((subject.id for subject in self.subjects))
        for status in SubjectWorkflowStatus.where(subject_ids=subject_ids, workflow_id=workflow_id):
            yield status

    def __contains__(self, subject):
        """
        A wrapper around :py:meth:`.LinkCollection.__contains__`. Equivalent
        to::

            subject in subject_set.links.subjects
        """
        return subject in self.links.subjects


LinkResolver.register(SubjectSet)
LinkResolver.register(SubjectSet, 'subject_set')
