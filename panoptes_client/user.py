from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import PanoptesObject, LinkResolver


class User(PanoptesObject):
    _api_slug = 'users'
    _link_slug = 'users'
    _edit_attributes = ()

    @property
    def avatar(self):
        """
        A dict containing metadata about the user's avatar.
        """

        return User.http_get('{}/avatar'.format(self.id))[0]

LinkResolver.register(User)
LinkResolver.register(User, 'owner')
