from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.utils import isiterable, split


class User(PanoptesObject):
    _api_slug = 'users'
    _link_slug = 'users'
    _edit_attributes = ()

    @classmethod
    def where(cls, **kwargs):
        email = kwargs.get('email')
        if not email:
            for user in super(User, cls).where(**kwargs):
                yield user
            return

        if not isiterable(email):
            email = [email]

        for batch in split(email, 50):
            kwargs['email'] = ",".join(batch)
            for user in super(User, cls).where(**kwargs):
                yield user

    @property
    def avatar(self):
        """
        A dict containing metadata about the user's avatar.
        """

        return User.http_get('{}/avatar'.format(self.id))[0]

LinkResolver.register(User)
LinkResolver.register(User, 'owner')
