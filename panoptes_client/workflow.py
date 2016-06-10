from panoptes_client.panoptes import PanoptesObject, LinkResolver

class Workflow(PanoptesObject):
    _api_slug = 'workflows'
    _link_slug = 'workflows'

LinkResolver.register(Workflow)
