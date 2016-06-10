from panoptes_client.panoptes import PanoptesObject, LinkResolver

class SubjectSet(PanoptesObject):
    _api_slug = 'subject_sets'
    _link_slug = 'subject_sets'

LinkResolver.register(SubjectSet)
