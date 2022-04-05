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
        subject_sets = [s.id if isinstance(
            s, SubjectSet) else s for s in subject_sets]
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
        """
        Adds selected Workflow to Caesar. Returns workflow as a dict from Caesar if successful.

        Examples::
            workflow.add_to_caesar()
        """
        payload = {
            'workflow': {
                'id': self.id
            }
        }
        return Caesar().http_post(self._api_slug, json=payload)[0]

    def subject_extracts(self, subject_id):
        """
        Returns a list of subject extracts as a dict from Caesar for a given subject.

        Examples::
            workflow.subject_extracts(1234)

            s = Subject(1234)
            workflow.subject_extracts(s.id)
        """
        url = f'{self._api_slug}/{self.id}/extractors/all/extracts'
        return Caesar().http_get(url, params={'subject_id': subject_id})[0]

    def subject_reductions(self, subject_id, reducer_key=""):
        """
        Returns a list of subject reductions as dicts from Caesar for a given subject.
        Defaults to return all subject reductions for a given subject.
        - **reducer_key** If reducer key is given, will filter and return reductions for the reducer with inputted reducer_key.

        Examples::
            workflow.subject_reductions(1234)
            workflow.subject_reductions(1234,'points')
        """
        url = f'{self._api_slug}/{self.id}/subjects/{subject_id}/reductions'
        if reducer_key and reducer_key.strip():
            url += f'?reducer_key={reducer_key.strip()}'
        return Caesar().http_get(url)[0]

    def extractors(self):
        """
        Returns a list of extractors as dicts from Caesar for particular workflow. 

        Examples::
            workflow.extractors()
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/extractors')[0]

    def reducers(self):
        """
        Returns a list of reducers as dicts from Caesar for particular workflow.

        Examples::
            workflow.reducers()
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/reducers')[0]

    def rules(self, rule_type):
        """
        Returns a list of Caesar workflow rules as dicts.

         - **rule_type** can either be 'subject' or 'user'; if 'subject' will return subject rules, if 'user' will return user rules

         Examples::
            workflow.rules('subject')
            workflow.rules('user')
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules')[0]

    def effects(self, rule_type, rule_id):
        """
        Returns a list of Caesar workflow effects as dicts for the workflow rule with id `rule_id`
        - **rule_type** can either be 'subject' or 'user'; if 'subject' will return effects of subject rules with id `rule_id`, if 'user' will return will return effects of user rules with id `rule_id`

        Examples::
            workflow.effects('subject', 123)
            workflow.effects('user', 321)
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects')[0]

    def add_extractor(self, extractor_type, extractor_key, task_key='T0', extractor_other_attributes=None):
        """
        Adds a Caesar extractor for given workflow. Will return extractor as a dict with 'id' if successful
        - **extractor_type** can be one of the following: 'blank', 'external', 'question', 'survey', 'who', 'pluck_field', or 'shape'
        - **extractor_key** is the unique key that you want to give to the extractor. The key will be used to track this specific reducer within Caesar.

        Examples::
            workflow.add_extractor('question', 'complete', 'T0', {'if_missing': ignore })
        """
        caesar = Caesar()
        caesar.validate_extractor_type(extractor_type)
        if extractor_other_attributes is None:
            extractor_other_attributes = {}
        payload = {
            'extractor': {
                'type': extractor_type,
                'key': extractor_key,
                'task_key': task_key,
                **extractor_other_attributes
            }
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/extractors', json=payload)[0]

    def add_reducer(self, reducer_type, key, other_reducer_attributes=None):
        """
        Adds a Caesar reducer for given workflow. Will return reducer as dict with 'id' if successful. 
        - **reducer_type** can be one of the following: 'consensus', 'count', 'placeholder', 'external', 'first_extract', 'stats', 'unique_count', 'rectangle', 'sqs'
        - **key** is a unique name for your reducer. This key will be used to track this specific reducer within Caesar.

        Examples::
            workflow.add_reducer('count', 'count', {'filters' : {'extractor_keys': ['complete']}})
        """
        caesar = Caesar()
        caesar.validate_reducer_type(reducer_type)
        if other_reducer_attributes is None:
            other_reducer_attributes = {}
        payload = {
            'reducer': {
                'type': reducer_type,
                'key': key,
                **other_reducer_attributes
            }
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/reducers', json=payload)[0]

    def add_rule(self, condition_string, rule_type):
        """
        Adds a Caesar rule for given workflow. Will return rule as a dict with 'id' if successful.
        - **condition_string** is  a string that represents a single operation (sometimes nested). The general syntax is like if you'd write Lisp in json. It is a stringified array with the first item being a string identifying the operator. See https://zooniverse.github.io/caesar/#rules for examples of condition strings
        - **rule_type** can either be 'subject' or 'user'


        Examples::
            workflow.add_rule('["gte", ["lookup", "complete.0", 0], ["const", 3]]', 'subject')

        """
        caesar = Caesar()
        caesar.validate_rule_type(rule_type)
        rules_payload = {
            'condition_string': condition_string
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/{rule_type}_rules', json={f'{rule_type}_rule': rules_payload})[0]

    def add_rule_effect(self, rule_type, rule_id, action, effect_config=None):
        """
        Adds a Caesar effect for workflow and given the workflow rule with id rule_id. Will return effect as a dict with 'id' if successful. 
        - **rule_type** can either be 'subject' or 'user'
        - **rule_id** is the id of the subject rule or user rule that the effect should run
        - **action** can be one of the following: 
            - **(actions for subject rules)** - 'retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'
            - **(actions for user rules)** - 'promote_user'

        Examples::
            workflow.add_rule_effect('subject', subject_rule['id'], 'retire_subject', {'reason': 'classification_count'})
        """
        caesar = Caesar()
        caesar.validate_rule_type(rule_type)
        caesar.validate_action(rule_type, action)
        if effect_config is None:
            effect_config = {}

        payload = {
            f'{rule_type}_rule_effect': {
                'action': action,
                'config': effect_config
            }
        }
        return caesar.http_post(f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects', json=payload)[0]

    @property
    def versions(self):
        """
        A generator which yields all :py:class:`.WorkflowVersion` instances for
        this workflow.
        """

        return WorkflowVersion.where(workflow=self)


LinkResolver.register(Workflow)
LinkResolver.register(Workflow, 'active_workflows', readonly=True)

# Keep import WorkflowVersion import on bottom to avoid circular import
from panoptes_client.workflow_version import WorkflowVersion
