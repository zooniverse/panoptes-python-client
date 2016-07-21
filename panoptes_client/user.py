from panoptes_client.panoptes import PanoptesObject, LinkResolver


class User(PanoptesObject):
    _api_slug = 'users'
    _link_slug = 'users'
    _edit_attributes = ()

LinkResolver.register(User)
