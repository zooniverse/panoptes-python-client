from panoptes_client.panoptes import Panoptes, PanoptesAPIException


class Caesar(object):
    """
    The low-level Caesar HTTP client class. Use this class to interact with the
    Caesar API. User credentials are shared with Panoptes, so log in via
    :py:meth:`.Panoptes.connect` before use.
    """
    EXTRACTOR_TYPES = ['blank', 'external', 'question', 'survey', 'who', 'pluck_field', 'shape']
    REDUCER_TYPES = [
        'consensus', 'count', 'placeholder', 'external', 'first_extract', 'stats',
        'unique_count', 'rectangle', 'sqs'
    ]
    RULE_TO_ACTION_TYPES = {
        'subject': ['retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'],
        'user': ['promote_user']
    }

    def __init__(
        self,
        endpoint='https://caesar.zooniverse.org',
        redirect_url='https://caesar.zooniverse.org/auth/zooniverse/callback'
    ):
        self.endpoint = endpoint
        self.headers = {
            'Accept': 'application/json'
        }

    def http_get(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        kwargs['headers'] = self.headers
        return Panoptes.client().get(*args, **kwargs)

    def http_post(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        kwargs['headers'] = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return Panoptes.client().post(*args, **kwargs)

    def http_put(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        kwargs['headers'] = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return Panoptes.client().put(*args, **kwargs)

    def http_delete(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        return Panoptes.client().delete(*args, **kwargs)

    def get_workflow(self, workflow_id):
        """
        Returns workflow object if exists in Caesar
        """
        return self.http_get(f'workflows/{workflow_id}')[0]

    def get_reductions_by_workflow_and_subject(self, workflow_id, subject_id):
        """
        Returns a list of all subject reductions as dicts from Caesar given the ids of the workflow and subject.
        """
        return self.http_get(f'workflows/{workflow_id}/subjects/{subject_id}/reductions')[0]

    def get_workflow_extractors(self, workflow_id):
        """
        Returns a list of extractors as dicts from Caesar for workflow with provided workflow_id
        """
        return self.http_get(f'workflows/{workflow_id}/extractors')[0]

    def get_workflow_reducers(self, workflow_id):
        """
        Returns a list of reducers as dicts from Caesar for workflow with provided workflow_id
        """
        return self.http_get(f'workflows/{workflow_id}/reducers')[0]

    def get_extracts_by_workflow_and_subject(self, workflow_id, subject_id):
        """
        Returns a list of extracts as dicts from Caesar for workflow with provided workflow_id
        """
        return self.http_get(
            f'workflows/{workflow_id}/extractors/extractor/extracts', params={'subject_id': subject_id})[0]

    def save_workflow(self, workflow_id, public_extracts=False, public_reductions=False):
        """
        Adds/updates workflow with provided workflow_id to Caesar. Checks to see if workflow exists in Caesar, if not
        then creates workflow and returns workflow as a dict from Caesar if created.
        If workflow is already in Caesar, will update the Caesar workflow.

        Examples::

            Caesar().save_workflow(123, public_extracts=True, public_reductions=True)
        """
        try:
            self.get_workflow(workflow_id)
        except PanoptesAPIException as err:
            if "couldn't find workflow with 'id'" in str(err).lower():
                return self.http_post('workflows', json={
                    'workflow': {
                        'id': workflow_id,
                        'public_extracts': public_extracts,
                        'public_reductions': public_reductions
                    }
                })[0]
            else:
                raise err
        else:
            return self.http_put(f'workflows/{workflow_id}', json={
                'workflow': {
                    'id': workflow_id,
                    'public_extracts': public_extracts,
                    'public_reductions': public_reductions
                }
            })[0]

    def create_workflow_extractor(self, workflow_id, extractor_key,
                                  extractor_type, task_key='T0', other_extractor_attributes=None):
        """
        Adds a Caesar extractor for workflow with id workflow_id. Will return extractor as a dict with 'id' if success.

        - **extractor_type** can be one of the following: 'blank', 'external', 'question', 'survey', 'who', 'pluck_field', or 'shape'
        - **extractor_key** is the unique key that you want to give to the extractor. The key will be used to track this specific reducer within Caesar.

        Examples::

            Caesar().create_workflow_extractor(12, 'question', 'complete', 'T0', {'if_missing': ignore })
        """

        self.validate_extractor_type(extractor_type)
        if other_extractor_attributes is None:
            other_extractor_attributes = {}

        payload = {
            'extractor': {
                'type': extractor_type,
                'key': extractor_key,
                'task_key': task_key,
                **other_extractor_attributes
            }
        }
        return self.http_post(f'workflows/{workflow_id}/extractors', json=payload)[0]

    def create_workflow_reducer(self, workflow_id, reducer_type, key, other_reducer_attributes=None):
        """
        Adds a Caesar reducer for given workflow. Will return reducer as dict with 'id' if successful.

        - **reducer_type** can be one of the following:
          'consensus', 'count', 'placeholder', 'external', 'first_extract',
          'stats', 'unique_count', 'rectangle', 'sqs'
        - **key** is a unique name for your reducer. This key will be used to track this specific reducer within Caesar.

        Examples::

            Caesar().create_workflow_reducer(1234, 'count', 'count', {'filters' : {'extractor_keys': ['complete']}})
        """

        self.validate_reducer_type(reducer_type)
        if other_reducer_attributes is None:
            other_reducer_attributes = {}

        payload = {
            'reducer': {
                'type': reducer_type,
                'key': key,
                **other_reducer_attributes
            }
        }

        return self.http_post(f'workflows/{workflow_id}/reducers', json=payload)[0]

    def create_workflow_rule(self, workflow_id, rule_type, condition_string='[]'):
        """
        Adds a Caesar rule for given workflow. Will return rule as a dict with 'id' if successful.

        - **condition_string** is  a string that represents a single operation (sometimes nested).
          The general syntax is like if you'd write Lisp in json.
          It is a stringified array with the first item being a string identifying the operator.
          See for examples of condition strings https://zooniverse.github.io/caesar/#rules
        - **rule_type** can either be 'subject' or 'user'

        Examples::

            caesar = Caesar()
            workflow = Workflow(1234)
            caesar.create_workflow_rule(workflow.id, 'subject','["gte", ["lookup", "complete.0", 0], ["const", 3]]')

        """

        self.validate_rule_type(rule_type)
        payload = {
            f'{rule_type}_rule': {
                'condition_string': condition_string
            }
        }
        return self.http_post(f'workflows/{workflow_id}/{rule_type}_rules', json=payload)[0]

    def create_workflow_rule_effect(self, workflow_id, rule_type, rule_id, action, config=None):
        """
        Adds a Caesar effect for workflow with id `workflow_id` and rule with id `rule_id`.
        Method will return effect as a dict with 'id' if successful.

        - **rule_type** can either be 'subject' or 'user'
        - **rule_id** is the id of the subject rule or user rule that the effect should run
        - **action** can be one of the following:
          - **(actions for subject rules)** - 'retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'
          - **(actions for user rules)** - 'promote_user'

        Examples::

            retirement_config = {'reason': 'classification_count'}
            Caesar().create_workflow_rule_effect(1, 'subject', subject_rule['id'], 'retire_subject', retirement_config)
        """

        self.validate_rule_type(rule_type)
        self.validate_action(rule_type, action)
        if config is None:
            config = {}
        payload = {
            f'{rule_type}_rule_effect': {
                'action': action,
                'config': config
            }
        }

        request_url = f'workflows/{workflow_id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects'
        return self.http_post(request_url, json=payload)[0]

    def import_data_extracts(self, workflow_id, csv_source):
        """
        Imports machine-learnt data extracts into Caesar.

        - **csv_source** must be a publicly accessible csv at the time of import.
          Eg. csv can be hosted via an AWS S3 Bucket, Azure Blob Storage, or Panoptes media item.
          See `this csv <https://panoptes-uploads-staging.zooniverse.org/project_attached_image/f1ab241f-2896-4efc-a1bc-3baaff64d783.csv>`_ as an example.
          `csv_source`'s csv must have header/titles/rows of the following:

          - `extractor_key` (key corresponding to the extractor in Caesar)
          - `subject_id`
          - `data` (the machine learnt data for the corresponding subject). This entry should be JSON.

          Example::

            caesar = Caesar(endpoint='https://caesar-staging.zooniverse.org')
            caesar.import_data_extracts(1234, 'https://panoptes-uploads-staging.zooniverse.org/project_attached_image/f1ab241f-2896-4efc-a1bc-3baaff64d783.csv')
        """
        return self.http_post(f'workflows/{workflow_id}/extracts/import', json={'file': csv_source})

    def validate_rule_type(self, rule_type):
        if rule_type not in self.RULE_TO_ACTION_TYPES.keys():
            raise ValueError(f'Invalid rule type: {rule_type}. Rule types can either be by "subject" or "user"')

    def validate_reducer_type(self, reducer_type):
        if reducer_type not in self.REDUCER_TYPES:
            raise ValueError('Invalid reducer type')

    def validate_extractor_type(self, extractor_type):
        if extractor_type not in self.EXTRACTOR_TYPES:
            raise ValueError('Invalid extractor type')

    def validate_action(self, rule_type, action):
        if action not in self.RULE_TO_ACTION_TYPES[rule_type]:
            raise ValueError('Invalid action for rule type')
