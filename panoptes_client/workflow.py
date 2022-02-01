from __future__ import absolute_import, division, print_function
from builtins import str
from copy import deepcopy
from panoptes_client.set_member_subject import SetMemberSubject
from panoptes_client.subject_workflow_status import SubjectWorkflowStatus

from panoptes_client.exportable import Exportable
from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject
from panoptes_client.subject_set import SubjectSet
from panoptes_client.utils import batchable

from panoptes_client.caesar import Caesar


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
            )
        },
    )

    def __init__(self, raw={}, etag=None):
        super(Workflow, self).__init__(raw, etag)
        if not self.configuration:
            self.configuration = {}
            self._original_configuration = {}
        if not self.retirement:
            self.retirement = {}
            self._original_retirement = {}
        if not self.tasks:
            self.tasks = {}
            self._original_tasks = {}

    def set_raw(self, raw, etag=None, loaded=True):
        super(Workflow, self).set_raw(raw, etag, loaded)
        if loaded:
            if self.configuration:
                self._original_configuration = deepcopy(self.configuration)
            if self.retirement:
                self._original_retirement = deepcopy(self.retirement)
            if self.tasks:
                self._original_tasks = deepcopy(self.tasks)
        elif loaded:
            self._original_configuration = None
            self._original_retirement = None
            self._original_tasks = None

    def save(self):
        """
        Adds workflow configuration, retirement, and tasks dicts to the list of
        savable attributes if it has changed.
        """
        if not self.configuration == self._original_configuration:
            self.modified_attributes.add('configuration')
        if not self.retirement == self._original_retirement:
            self.modified_attributes.add('retirement')
        if not self.tasks == self._original_tasks:
            self.modified_attributes.add('tasks')

        super(Workflow, self).save()

    @batchable
    def retire_subjects(self, subjects, reason='other'):
        """
        Retires subjects in this workflow.

        - **subjects** can be a list of :py:class:`Subject` instances, a list
          of subject IDs, a single :py:class:`Subject` instance, or a single
          subject ID.
        - **reason** gives the reason the :py:class:`Subject` has been retired.
          Defaults to **other**.

        Examples::

            workflow.retire_subjects(1234)
            workflow.retire_subjects([1,2,3,4])
            workflow.retire_subjects(Subject(1234))
            workflow.retire_subjects([Subject(12), Subject(34)])
        """

        subjects = [s.id if isinstance(s, Subject) else s for s in subjects]

        return Workflow.http_post(
            '{}/retired_subjects'.format(self.id),
            json={
                'subject_ids': subjects,
                'retirement_reason': reason
            },
        )

    @batchable
    def unretire_subjects(self, subjects):
        """
        Un-retires subjects in this workflow by subjects.

        - **subjects** can be a list of :py:class:`Subject` instances, a list
          of subject IDs, a single :py:class:`Subject` instance, or a single
          subject ID.
        """

        subjects = [s.id if isinstance(s, Subject) else s for s in subjects]
        return Workflow.http_post(
            '{}/unretire_subjects'.format(self.id),
            json={
                'subject_ids': subjects
            },
        )

    @batchable
    def unretire_subjects_by_subject_set(self, subject_sets):
        """
        Un-retires subjects in this workflow by subject_sets.
         - **subjects_sets* can be a list of :py:class:`SubjectSet` instances, a list
          of subject_set IDs, a single :py:class:`SubjectSet` instance, or a single
          subject_set ID.
        """
        subject_sets = [s.id if isinstance(s, SubjectSet) else s for s in subject_sets]
        return Workflow.http_post(
            '{}/unretire_subjects'.format(self.id),
            json={
                'subject_set_ids': subject_sets
            },
        )

    def add_subject_sets(self, subject_sets):
        """
        A wrapper around :py:meth:`.LinkCollection.add`. Equivalent to::

            workflow.links.subject_sets.add(subject_sets)
        """

        return self.links.subject_sets.add(subject_sets)

    def remove_subject_sets(self, subject_sets):
        """
        A wrapper around :py:meth:`.LinkCollection.remove`. Equivalent to::

            workflow.links.subject_sets.remove(subject_sets)
        """

        return self.links.subject_sets.remove(subject_sets)

    def subject_workflow_status(self, subject_id):
        """
        Returns SubjectWorkflowStatus of the current workflow given subject_id

        Example::

            workflow.subject_workflow_status(1234)
        """
        return next(SubjectWorkflowStatus.where(subject_id=subject_id, workflow_id=self.id))

    def subject_workflow_statuses(self, subject_set_id):
        """
        A generator which yields :py:class:`.SubjectWorkflowStatus` objects for subjects in the
        subject set of the given workflow

        Examples::

            for status in workflow.subject_workflow_statuses(1234):
                print(status.retirement_reason)
        """
        subject_ids = []
        for sms in SetMemberSubject.where(subject_set_id=subject_set_id):
            subject_ids.append(sms.links.subject.id)

        subject_ids = ','.join(map(str, subject_ids))
        for status in SubjectWorkflowStatus.where(subject_ids=subject_ids, workflow_id=self.id):
            yield status
    
    """ CAESAR METHODS """

    def add_to_caesar(self):
        caesar = Caesar()
        payload={
            'workflow': {
                'id': self.id
            }
        }
        return caesar.http_post(self._api_slug, json=payload)

    def subject_reductions(self, subject_id, reducer_key=""):
        #returns all reductions of all reducers if no reducer key given
        caesar = Caesar()
        url = f'{self._api_slug}/{self.id}/subjects/{subject_id}/reductions'
        if reducer_key and reducer_key.strip():
            url += f'?reducer_key={reducer_key.strip()}'
        return caesar.http_get(url)[0]
    
    def extractors(self):
        caesar = Caesar()
        return caesar.http_get(f'{self._api_slug}/{self.id}/extractors')[0]
    
    def reducers(self):
        caesar = Caesar()
        return caesar.http_get(f'{self._api_slug}/{self.id}/reducers')[0]
    
    def rules(self, rule_type):
        RULE_TYPES = ['subject', 'user']
        if rule_type not in RULE_TYPES:
            raise ValueError(f'Invalid rule type: {rule_type} . Can only create "subject" rules or "user" rules.')
        
        caesar = Caesar()
        return caesar.http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules')[0]
    
    def effects(self, rule_type, rule_id):
        RULE_TYPES = ['subject', 'user']
        if rule_type not in RULE_TYPES:
            raise ValueError(f'Invalid rule type: {rule_type} . Can only create "subject" rules or "user" rules.')
        caesar = Caesar()
        return caesar.http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects')[0]

    def add_extractor(self, extractor_type, extractor_key, task_key='T0', extractor_other_attributes={}):
        EXTRACTOR_TYPES = ['blank', 'external', 'question', 'survey', 'who', 'pluck_field', 'shape']
        if extractor_type not in EXTRACTOR_TYPES:
            raise ValueError('Invalid extractor type')

        caesar = Caesar()
        payload = {
            'extractor': {
                'type': extractor_type,
                'key': extractor_key,
                'task_key': task_key,
                **extractor_other_attributes
            }
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/extractors', json=payload)
    
    def add_reducer(self, reducer_type, key, other_reducer_attributes={}):
        REDUCER_TYPES = ['consensus', 'count', 'placeholder', 'external', 'first_extract', 'stats', 'unique_count', 'rectangle', 'sqs']
        if reducer_type not in REDUCER_TYPES:
            raise ValueError('Invalid reducer type')

        caesar = Caesar()
        payload = {
            'reducer': {
                'type': reducer_type,
                'key': key,
                **other_reducer_attributes
            }
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/reducers', json=payload)
    
    def add_rule(self,condition_string, rule_type):
        caesar = Caesar()
        RULE_TYPES = ['subject', 'user']
        if rule_type not in RULE_TYPES:
            raise ValueError(f'Invalid rule type: {rule_type} . Can only create "subject" rules or "user" rules.')

        rules_payload={
            'condition_string': condition_string
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/{rule_type}_rules', json={f'{rule_type}_rule': rules_payload})
    
    def add_rule_effect(self, rule_type, rule_id, action, effect_config={}):
        caesar = Caesar()     
        RULE_TO_ACTION_TYPES = {
            'subject': ['retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'], 
            'user': ['promote_user']
        }

        if rule_type not in RULE_TO_ACTION_TYPES.keys() or action not in RULE_TO_ACTION_TYPES[rule_type]:
            raise ValueError('Invalid rule type or action')
        
        payload = {
            f'{rule_type}_rule_effect': {
                'action': action,
                'config': effect_config
            }
        }
        
        return caesar.http_post(f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects', json=payload)

    @property
    def versions(self):
        """
        A generator which yields all :py:class:`.WorkflowVersion` instances for
        this workflow.
        """

        return WorkflowVersion.where(workflow=self)


LinkResolver.register(Workflow)
LinkResolver.register(Workflow, 'active_workflows', readonly=True)

from panoptes_client.workflow_version import WorkflowVersion
