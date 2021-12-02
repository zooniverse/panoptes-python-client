from panoptes_client.panoptes import Panoptes

class Caesar(object):
    def __init__(self, endpoint =  'https://caesar-staging.zooniverse.org', redirect_url= 'https://caesar.zooniverse.org/auth/zooniverse/callback'):
        self.endpoint = endpoint
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def http_get(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
        kwargs['headers'] = self.headers
        return Panoptes.client().get(*args, **kwargs)

    def http_post(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
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
        return self.http_get(f'workflows/{workflow_id}/subjects/{subject_id}')