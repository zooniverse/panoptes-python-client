from panoptes_client.panoptes import Panoptes, PanoptesObject

class Caesar(object):
    def __init__(self, endpoint =  'https://caesar-staging.zooniverse.org', redirect_url= 'https://caesar.zooniverse.org/auth/zooniverse/callback'):
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
    
    def get_workflow_by_id(self, workflow_id):
        return self.http_get(f'workflows/{workflow_id}')

    def get_reductions_by_workflow_and_subject(self, workflow_id, subject_id):
        return self.http_get(f'workflows/{workflow_id}/subjects/{subject_id}/reductions')
    
    def get_workflow_extractors(self, workflow_id):
        return self.http_get(f'workflows/{workflow_id}/extractors')
    
    def get_workflow_reducers(self, workflow_id):
        return self.http_get(f'workflows/{workflow_id}/reducers')
    
    def get_extracts_by_workflow_and_subject(self, workflow_id, subject_id):
        return self.http_get(f'workflows/{workflow_id}/extractors/extractor/extracts', params={'subject_id' : subject_id})

    def get_extractor_by_workflow_and_id(self, workflow_id, extractor_id):
        return self.http_get(f'workflows/{workflow_id}/extractors/{extractor_id}')
    
    def create_workflow_extractor(self, workflow_id, extractor_payload={}):
        # accepted extractor_types ["blank", external, question, survey, who, pluck_field, shape]
        # extractor_payload must have 'type', eg { 'type' : 'blank', 'key' : 'extractor_key', 'task_key': 'T0'}
        return self.http_post(f'workflows/{workflow_id}/extractors', json={'extractor': extractor_payload})
    
    def create_workflow_reducer(self, workflow_id, reducer_payload={}):
        return self.http_post(f'workflows/{workflow_id}/reducers', json={'reducer': reducer_payload })

    @classmethod
    def url(cls, *args):
        return '/'.join(['', cls._api_slug] + [str(a) for a in args if a])
