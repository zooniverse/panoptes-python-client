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

        - **subjects_sets** can be a list of :py:class:`SubjectSet` instances, a
          list of subject_set IDs, a single :py:class:`SubjectSet` instance, or
          a single subject_set ID.
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

    def save_to_caesar(self, public_extracts=False, public_reductions=False):
        """
        Adds/updates selected Workflow to Caesar. Returns workflow as a dict from Caesar if created.

        - **public_extracts** set to True to Enable Public Extracts, Defaults to False
        - **public_reductions** set to True to Enable Public Reductions. Defaults to False

        Examples::

            workflow.save_to_caesar()
            workflow.save_to_caesar(public_extracts=True, public_reductions=True)

        """
        return Caesar().save_workflow(self.id, public_extracts, public_reductions)

    def caesar_subject_extracts(self, subject_id):
        """
        Returns a list of subject extracts as a dict from Caesar for a given subject.

        Examples::

            workflow.caesar_subject_extracts(1234)

            s = Subject(1234)
            workflow.caesar_subject_extracts(s.id)
        """
        url = f'{self._api_slug}/{self.id}/extractors/all/extracts'
        return Caesar().http_get(url, params={'subject_id': subject_id})[0]

    def caesar_subject_reductions(self, subject_id, reducer_key=""):
        """
        Returns a list of subject reductions as dicts from Caesar for a given subject.
        Defaults to return all subject reductions for a given subject.

        - **reducer_key** If given, will filter and return reductions for the reducer with that reducer_key.

        Examples::

            workflow.caesar_subject_reductions(1234)
            workflow.caesar_subject_reductions(1234,'points')
        """
        url = f'{self._api_slug}/{self.id}/subjects/{subject_id}/reductions'
        if reducer_key.strip():
            url += f'?reducer_key={reducer_key.strip()}'
        return Caesar().http_get(url)[0]

    def caesar_extractors(self):
        """
        Returns a list of extractors as dicts from Caesar for particular workflow.

        Examples::

            workflow.caesar_extractors()
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/extractors')[0]

    def caesar_reducers(self):
        """
        Returns a list of reducers as dicts from Caesar for particular workflow.

        Examples::

            workflow.caesar_reducers()
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/reducers')[0]

    def caesar_rules(self, rule_type):
        """
        Returns a list of Caesar workflow rules as dicts.

        - **rule_type** can either be 'subject' or 'user';
          if 'subject' will return subject rules,
          if 'user' will return user rules

        Examples::

            workflow.caesar_rules('subject')
            workflow.caesar_rules('user')
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules')[0]

    def caesar_effects(self, rule_type, rule_id):
        """
        Returns a list of Caesar workflow effects as dicts for the workflow rule with id `rule_id`.

        - **rule_type** can either be 'subject' or 'user';
          if 'subject' will return effects of subject rules with id `rule_id`,
          if 'user' will return will return effects of user rules with id `rule_id`

        Examples::

            workflow.caesar_effects('subject', 123)
            workflow.caesar_effects('user', 321)
        """
        return Caesar().http_get(f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects')[0]

    def add_caesar_extractor(self, extractor_type, extractor_key, task_key='T0', extractor_other_attributes=None):
        """
        Adds a Caesar extractor for given workflow. Will return extractor as a dict with 'id' if successful.

        - **extractor_type** can be one of the following:
            'blank', 'external', 'question', 'survey', 'who', 'pluck_field', or 'shape'
        - **extractor_key** is the unique key that you want to give to the extractor.
            The key will be used to track this specific reducer within Caesar.

        Examples::

            workflow.add_caesar_extractor('question', 'complete', 'T0', {'if_missing': ignore })
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

    def add_caesar_reducer(self, reducer_type, key, other_reducer_attributes=None):
        """
        Adds a Caesar reducer for given workflow. Will return reducer as dict with 'id' if successful.

        - **reducer_type** can be one of the following:
            'consensus', 'count', 'placeholder', 'external', 'first_extract',
            'stats', 'unique_count', 'rectangle', 'sqs'
        - **key** is a unique name for your reducer. This key will be used to track this specific reducer within Caesar.

        Examples::

            workflow.add_caesar_reducer('count', 'count', {'filters' : {'extractor_keys': ['complete']}})
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

    def add_caesar_rule(self, condition_string, rule_type):
        """
        Adds a Caesar rule for given workflow. Will return rule as a dict with 'id' if successful.

        - **condition_string** is  a string that represents a single operation (sometimes nested).
            The general syntax is like if you'd write Lisp in json.
            It is a stringified array with the first item being a string identifying the operator.
            See https://zooniverse.github.io/caesar/#rules for examples of condition strings
        - **rule_type** can either be 'subject' or 'user'

        Examples::

            workflow.add_caesar_rule('["gte", ["lookup", "complete.0", 0], ["const", 3]]', 'subject')

        """
        caesar = Caesar()
        caesar.validate_rule_type(rule_type)
        payload = {f'{rule_type}_rule': {
            'condition_string': condition_string
        }}
        return caesar.http_post(f'{self._api_slug}/{self.id}/{rule_type}_rules', json=payload)[0]

    def add_caesar_rule_effect(self, rule_type, rule_id, action, effect_config=None):
        """
        Adds a Caesar effect for workflow and given the workflow rule with id rule_id.
        Method will return effect as a dict with 'id' if successful.

        - **rule_type** can either be 'subject' or 'user'
        - **rule_id** is the id of the subject rule or user rule that the effect should run
        - **action** can be one of the following:
            - **(actions for subject rules)** - 'retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'
            - **(actions for user rules)** - 'promote_user'

        Examples::

            workflow.add_caesar_rule_effect('subject', subject_rule['id'], 'retire_subject',
                                    {'reason': 'classification_count'})
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
        return caesar.http_post(
            f'{self._api_slug}/{self.id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects',
            json=payload
        )[0]

    def import_caesar_data_extracts(self, csv_source):
        """
        Imports machine-learnt data as extracts into Caesar.

        - **csv_source** must be a publicly accessible csv at the time of import.
          Eg. csv can be hosted via an AWS S3 Bucket, Azure Blob Storage, or Panoptes media item.
          See `this csv <https://panoptes-uploads-staging.zooniverse.org/project_attached_image/f1ab241f-2896-4efc-a1bc-3baaff64d783.csv>`_ as an example.
          `csv_source`'s csv must have header/titles/rows of the following:

          - `extractor_key` (key corresponding to the extractor in Caesar)
          - `subject_id`
          - `data` (the machine learnt data for the corresponding subject)

        Example::

            workflow.import_caesar_data_extracts('https://panoptes-uploads-staging.zooniverse.org/project_attached_image/f1ab241f-2896-4efc-a1bc-3baaff64d783.csv')
        """
        return Caesar().http_post(f'{self._api_slug}/{self.id}/extracts/import', json={'file': csv_source})

    def add_alice_extractors(self, alice_task_key='T0', question_task_key='T1',
                             question_extractor_if_missing='ignore',
                             other_question_extractor_attrib=None,
                             other_alice_extractor_attrib=None):
        """
        Adds ALICE Extractors (two extractors: Question and External).

        - QuestionExtractor getting created will have a key of `complete`
        - **question_task_key** - Task ID that reflects placement of:
          “Have all the volunteer-made underline marks turned grey?” step. Defaults to T1
        - ExternalExtractor getting created will have a key of `alice`
        - **alice_task_key** - Task ID that reflects placement of Transcription Task step (Defaults to T0)

        Examples::

            workflow.add_alice_extractors()
        """
        if other_question_extractor_attrib is None:
            other_question_extractor_attrib = {}

        if other_alice_extractor_attrib is None:
            other_alice_extractor_attrib = {}

        question_extractor_attributes = {
            'if_missing': question_extractor_if_missing,
            **other_question_extractor_attrib
        }

        alice_extractor_attributes = {
            'url': f'https://aggregation-caesar.zooniverse.org/extractors/line_text_extractor?task={alice_task_key}',
            **other_alice_extractor_attrib
        }

        self.add_caesar_extractor('question', 'complete', question_task_key, question_extractor_attributes)
        self.add_caesar_extractor('external', 'alice', alice_task_key, alice_extractor_attributes)

    def add_alice_reducers(self, alice_min_views=5, low_consensus_threshold=3):
        """
        Adds ALICE Reducers for given workflow (three reducers: External, Stats, Count).

        - **alice_min_views** - This is the threshold number of classifications in order to "gray-out" a transcribed line.
          Default is 5.
        - **low_consensus_threshold** - This is the threshold number of classifications in agreement for good consensus.
          Default is 3
        """
        external_reducer_url = 'https://aggregation-caesar.zooniverse.org/reducers/optics_line_text_reducer'
        if alice_min_views or low_consensus_threshold:
            external_reducer_url += f'?minimum_views={alice_min_views}&'
            external_reducer_url += f'low_consensus_threshold={low_consensus_threshold}'

        default_filter_attribs = {
            'repeated_classifications': 'keep_first'
        }
        external_reducer_attributes = {
            'url': external_reducer_url,
            'filters': {
                'extractor_keys': ['alice'],
                **default_filter_attribs
            }
        }
        self.add_caesar_reducer('external', 'alice', external_reducer_attributes)

        complete_reducer_attribs = {
            'filters': {
                'extractor_keys': ['complete'],
                **default_filter_attribs
            }
        }
        self.add_caesar_reducer('stats', 'complete', complete_reducer_attribs)

        self.add_caesar_reducer('count', 'count', complete_reducer_attribs)

    def add_alice_rules_and_effects(self, question_retirement_limit=3, count_retirement_limit=30):
        """
        Adds subject rules and corresponding effects for ALICE configuration of the given workflow.
        Two subject rules are created that will trigger retirement: a Question rule and a Count rule.
        A total of 4 subject rule effects should get created.
        There should be 2 effects related to the Question Rule condition
        (one to send to ALICE and the other to retire subject).
        There should also be 2 effects related to the Count Rule condition
        (one to send to alice and the other to retire subject)

        - **question_retirement_limit** - Question subject rule created will trigger retirement when the answer to:
          "is this complete" question reaches this threshhold limit (defaults to 3)
        - **count_retirement_limit** - Count Subject Rule created will trigger retirement when the classification count reaches this limit (defaults to 30)

        """
        question_subject_rule = self.add_caesar_rule(
            f'["gte", ["lookup", "complete.0", 0], ["const", {question_retirement_limit}]]',
            'subject'
        )
        send_to_alice_effect_config = {
            'url': 'https://tove.zooniverse.org/import',
            'reducer_key': 'alice'
        }
        self.add_caesar_rule_effect('subject', question_subject_rule['id'], 'external', send_to_alice_effect_config)
        self.add_caesar_rule_effect('subject', question_subject_rule['id'], 'retire_subject', {'reason': 'consensus'})

        count_subject_rule = self.add_caesar_rule(
            f'["gte", ["lookup", "count.classifications", 0], ["const", {count_retirement_limit}]]',
            'subject'
        )
        self.add_caesar_rule_effect('subject', count_subject_rule['id'], 'external', send_to_alice_effect_config)
        self.add_caesar_rule_effect('subject', count_subject_rule['id'], 'retire_subject', {'reason': 'classification_count'})

    def configure_for_alice(self):
        """
        Configures workflow for ALICE/TOVE.

        - This method will add workflow to Caesar
        - This method will create Caesar Extractors needed for ALICE with defaults.
        - This method will also create Caesar Reducers needed for ALICE with defaults.
          (In particular, `minimum_views` = 5, and `low_consensus_threshold` = 3)
        - And this method will also create Caesar Subject Rules and Effects needed for ALICE with defaults.
          (In particular, Question-based retirement's retirement limit is 3 and Count-based retirement default is 30.)

        """
        self.save_to_caesar(public_extracts=True, public_reductions=True)
        self.add_alice_extractors()
        self.add_alice_reducers()
        self.add_alice_rules_and_effects()

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
