from panoptes_client.workflow import Workflow
from panoptes_client.project import Project

from panoptes_client.panoptes import (
    LinkResolver, PanoptesAPIException, PanoptesObject
)

class Classification(PanoptesObject):
    _api_slug = 'classifications'
    _link_slug = 'classification'
    _edit_attributes = ( )

    def __init__(self, record):
        super(Classification, self).__init__(record)
        self.build_from_record(record)

    def build_from_record(self, record):
        self.id = record['data']['id']
        self.gold_standard = True if record['data']['gold_standard'] else False
        self.annotations = record['data']['annotations']
        self.project = Project.find(record['data']['links']['project'])
        self.workflow = Workflow.find(record['data']['links']['workflow'])

LinkResolver.register(Classification)
