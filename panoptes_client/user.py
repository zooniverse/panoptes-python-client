from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.utils import isiterable, split

BATCH_SIZE = 50

class User(PanoptesObject):
    _api_slug = 'users'
    _link_slug = 'users'
    _edit_attributes = (
      'valid_email',
    )

    @classmethod
    def where(cls, **kwargs):
        email = kwargs.get('email')
        login = kwargs.get('login')

        if email and login:
            raise ValueError(
                'Queries are supported on at most ONE of email and login'
            )

        # This is a workaround for
        # https://github.com/zooniverse/Panoptes/issues/2733
        kwargs['page_size'] = BATCH_SIZE

        if email:
            if not isiterable(email):
                email = [email]

            for batch in split(email, BATCH_SIZE):
                kwargs['email'] = ",".join(batch)
                for user in super(User, cls).where(**kwargs):
                    yield user

        elif login:
            if not isiterable(login):
                login = [login]

            for batch in split(login, BATCH_SIZE):
                kwargs['login'] = ",".join(batch)
                for user in super(User, cls).where(**kwargs):
                    yield user

        else:
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
