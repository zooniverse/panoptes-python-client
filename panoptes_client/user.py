from panoptes_client.panoptes import PanoptesObject, LinkResolver


class User(PanoptesObject):
    _api_slug = 'users'
    _link_slug = 'users'
    _edit_attributes = ()

    def avatar(self):
        return User.http_get('{}/avatar'.format(self.id))[0]

LinkResolver.register(User)
LinkResolver.register(User, 'owner')
