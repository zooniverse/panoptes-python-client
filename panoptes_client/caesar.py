from panoptes_client.panoptes import Panoptes


class Caesar(object):
    EXTRACTOR_TYPES = ['blank', 'external', 'question', 'survey', 'who', 'pluck_field', 'shape']
    REDUCER_TYPES = ['consensus', 'count', 'placeholder', 'external', 'first_extract', 'stats', 'unique_count', 'rectangle', 'sqs']
    RULE_TO_ACTION_TYPES = {
        'subject': ['retire_subject', 'add_subject_to_set', 'add_to_collection', 'external'],
        'user': ['promote_user']
    }

    def __init__(self, endpoint='https://caesar-staging.zooniverse.org', redirect_url='https://caesar.zooniverse.org/auth/zooniverse/callback'):
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
        return Panoptes.client().put(*args, **kwargs)

    def http_delete(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        return Panoptes.client().delete(*args, **kwargs)

    def get_reductions_by_workflow_and_subject(self, workflow_id, subject_id):
        return self.http_get(f'workflows/{workflow_id}/subjects/{subject_id}/reductions')

    def get_workflow_extractors(self, workflow_id):
        return self.http_get(f'workflows/{workflow_id}/extractors')

    def get_workflow_reducers(self, workflow_id):
        return self.http_get(f'workflows/{workflow_id}/reducers')

    def get_extracts_by_workflow_and_subject(self, workflow_id, subject_id):
        return self.http_get(f'workflows/{workflow_id}/extractors/extractor/extracts', params={'subject_id': subject_id})

    def get_extractor_by_workflow_and_id(self, workflow_id, extractor_id):
        return self.http_get(f'workflows/{workflow_id}/extractors/{extractor_id}')

    def add_workflow(self, workflow_id):
        return self.http_post('workflows', json={'workflow': {'id': workflow_id}})

    def create_workflow_extractor(self, workflow_id, extractor_key, extractor_type, task_key='T0', other_extractor_attributes={}):
        self.validate_extractor_type(extractor_type)
        payload = {
            'extractor': {
                'type': extractor_type,
                'key': extractor_key,
                'task_key': task_key,
                **other_extractor_attributes
            }
        }
        return self.http_post(f'workflows/{workflow_id}/extractors', json=payload)

    def create_workflow_reducer(self, workflow_id, reducer_type, key, other_reducer_attributes={}):
        self.validate_reducer_type(reducer_type)
        payload = {
            'reducer': {
                'type': reducer_type,
                'key': key,
                **other_reducer_attributes
            }
        }

        return self.http_post(f'workflows/{workflow_id}/reducers', json=payload)

    def create_workflow_rule(self, workflow_id, rule_type, condition_string='[]'):
        self.validate_rule_type(rule_type)

        # condition string e.g.'["gte", ["lookup", "count.classifications", 0], ["const", 30]]'
        payload = {f'{rule_type}_rule': {
                'condition_string': condition_string
            }
        }
        return self.http_post(f'workflows/{workflow_id}/{rule_type}_rules', json=payload)

    def create_workflow_rule_effect(self, workflow_id, rule_type, rule_id, action, config={}):
        self.validate_rule_type(rule_type)
        self.validate_action(action)
        payload = {
            f'{rule_type}_rule_effect': {
                'action': action,
                'config': config
            }
        }

        request_url = f'workflows/{workflow_id}/{rule_type}_rules/{rule_id}/{rule_type}_rule_effects'
        return self.http_post(request_url, json=payload)

    def validate_rule_type(self, rule_type):
        if rule_type not in self.RULE_TO_ACTION_TYPES.keys():
            raise ValueError(f'Invalid rule type: {rule_type}.  Rule types can either be by "subject" or "user" ')

    def validate_reducer_type(self, reducer_type):
        if reducer_type not in self.REDUCER_TYPES:
            raise ValueError('Invalid reducer type')

    def validate_extractor_type(self, extractor_type):
        if extractor_type not in self.EXTRACTOR_TYPES:
            raise ValueError('Invalid extractor type')

    def validate_action(self, rule_type, action):
        if action not in self.RULE_TO_ACTION_TYPES[rule_type]:
            raise ValueError('Invalid action for rule type')
