from panoptes_client.panoptes import LinkResolver, PanoptesObject

class Classification(PanoptesObject):
    _api_slug = 'classifications'
    _link_slug = 'classification'
    _edit_attributes = ( )

LinkResolver.register(Classification)
