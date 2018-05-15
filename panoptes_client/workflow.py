from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.exportable import Exportable
from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject
from panoptes_client.subject_set import SubjectSet
from panoptes_client.utils import batchable


class Workflow(PanoptesObject, Exportable):
    _api_slug = 'workflows'
    _link_slug = 'workflows'
    _edit_attributes = (
        'active',
        'configuration',
        'display_name',
        'first_task',
        'mobile_friendly',
        'primary_language',
        'retirement',
        'tasks',
        {
            'links': (
                'project',
            ),
        }
    )

    @batchable
    def retire_subjects(self, subjects, reason='other'):
        """
        Retires subjects in this workflow.

        - **subjects** can be a list of Subject instances, a list of subject
          IDs, a single Subject instance, or a single subject ID.
        - **reason** gives the reason the subject has been retired. Defaults to
          **other**.

        Examples::

            workflow.retire_subjects(1234)
            workflow.retire_subjects([1,2,3,4])
            workflow.retire_subjects(Subject(1234))
            workflow.retire_subjects([Subject(12), Subject(34)])
        """

        subjects = [ s.id if isinstance(s, Subject) else s for s in subjects ]

        return Workflow.http_post(
            '{}/retired_subjects'.format(self.id),
            json={
                'subject_ids': subjects,
                'retirement_reason': reason
            }
        )

    @batchable
    def add_subject_sets(self, subject_sets):
        """
        Links the given subject sets to this workflow.

        - **subject_sets** can be a list of SubjectSet instances, a list of
          subject set IDs, a single SubjectSet instance, or a single subject
          set ID.

        Examples::

            workflow.add_subject_sets(1234)
            workflow.add_subject_sets([1,2,3,4])
            workflow.add_subject_sets(SubjectSet(1234))
            workflow.add_subject_sets([SubjectSet(12), SubjectSet(34)])
        """

        _subject_sets = self._build_subject_set_list(subject_sets)

        return Workflow.http_post(
            '{}/links/subject_sets'.format(self.id),
            json={'subject_sets': _subject_sets}
        )

    @batchable
    def remove_subject_sets(self, subject_sets):
        """
        Unlinks the given subject sets from this workflow.

        - **subject_sets** can be a list of SubjectSet instances, a list of
          subject set IDs, a single SubjectSet instance, or a single subject
          set ID.

        Examples::

            workflow.remove_subject_sets(1234)
            workflow.remove_subject_sets([1,2,3,4])
            workflow.remove_subject_sets(SubjectSet(1234))
            workflow.remove_subject_sets([SubjectSet(12), SubjectSet(34)])
        """

        _subject_sets = self._build_subject_set_list(subject_sets)
        _subject_set_ids = ",".join(_subject_sets)

        self.http_delete(
            '{}/links/subject_sets/{}'.format(self.id, _subject_set_ids)
        )

    def _build_subject_set_list(self, subject_sets):
        _subject_sets = []
        for subject_set in subject_sets:
            if not (
                isinstance(subject_set, SubjectSet)
                or isinstance(subject_set, (int, str,))
            ):
                raise TypeError

            if isinstance(subject_set, SubjectSet):
                _subject_set_id = subject_set.id
            else:
                _subject_set_id = str(subject_set)

            _subject_sets.append(_subject_set_id)

        return _subject_sets

    @property
    def versions(self):
        """
        A generator which yields all :py:class:`.WorkflowVersion` instances for
        this workflow.
        """

        return WorkflowVersion.where(workflow=self)

LinkResolver.register(Workflow)

from panoptes_client.workflow_version import WorkflowVersion
