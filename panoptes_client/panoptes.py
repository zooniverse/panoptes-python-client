from __future__ import absolute_import, division, print_function
from builtins import str

import logging
import os
import requests

from datetime import datetime, timedelta

if os.environ.get('PANOPTES_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)


class Panoptes(object):
    """
    The low-level Panoptes HTTP client class. You should never need to manually
    create an instance of this class, but you will need to import it to log in,
    etc.
    """

    _client = None

    _http_headers = {
        'default': {
            'Accept': 'application/vnd.api+json; version=1',
        },
        'GET': {},
        'PUT': {
            'Content-Type': 'application/json',
        },
        'POST': {
            'Content-Type': 'application/json',
        },
        'DELETE': {
            'Content-Type': 'application/json',
        },
    }

    _endpoint_client_ids = {
        'default': (
            'ce310d45f951de68c4cc8ef46ca38cc0a008f607a2026680295757bfef99f43c'
        ),
        'https://panoptes-staging.zooniverse.org': (
            'e094b63362fdef0548e0bbcc6e6cb5996c422d3a770074ef972432d57d41049c'
        ),
    }

    @classmethod
    def connect(cls, *args, **kwargs):
        """
        connect(username=None, password=None, endpoint=None, admin=False)

        Configures the Panoptes client for use.

        Note that there is no need to call this unless you need to pass one or
        more of the below arguments.  By default, the client will connect to
        the public Zooniverse.org API as an anonymous user.

        Also note that this method only *stores* the given values. It does not
        immediately perform any authentication or attempt to connect to the
        API. If the given credentials are incorrect, the client will raise a
        PanoptesAPIException the first time it makes a request to the API.

        All arguments are optional:

        - **username** is your Zooniverse.org username.
        - **password** is your Zooniverse.org password.
        - **endpoint** is the HTTP API endpoint you'd like to connect to.
          Defaults to **https://www.zooniverse.org**. Should not include a
          trailing slash.
        - **admin** is a boolean, switching on admin mode if ``True``. Has no
          effect if the given username is not a Zooniverse.org administrator.


        Examples::

            Panoptes.connect(username='example', password='example')
            Panoptes.connect(endpoint='https://panoptes.example.com')
        """
        return cls(*args, **kwargs)

    @classmethod
    def client(cls):
        if not cls._client:
            cls._client = cls()
        return cls._client

    def __init__(
        self,
        endpoint=None,
        client_id=None,
        client_secret=None,
        redirect_url=None,
        username=None,
        password=None,
        admin=False
    ):
        Panoptes._client = self

        self.endpoint = endpoint or os.environ.get(
            'PANOPTES_ENDPOINT',
            'https://www.zooniverse.org'
        )
        self.username = username or os.environ.get('PANOPTES_USERNAME')
        self.password = password or os.environ.get('PANOPTES_PASSWORD')
        self.redirect_url = \
            redirect_url or os.environ.get('PANOPTES_REDIRECT_URL')
        self.client_secret = \
            client_secret or os.environ.get('PANOPTES_CLIENT_SECRET')

        if client_id:
            self.client_id = client_id
        elif os.environ.get('PANOPTES_CLIENT_ID'):
            self.client_id = os.environ.get('PANOPTES_CLIENT_ID')
        else:
            self.client_id = self._endpoint_client_ids.get(
                self.endpoint,
                self._endpoint_client_ids['default']
            )

        self.logged_in = False
        self.bearer_token = None
        self.admin = admin

        self.session = requests.session()

        self.logger = logging.getLogger('panoptes_client')

    def http_request(
        self,
        method,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        _headers = self._http_headers['default'].copy()
        _headers.update(self._http_headers[method])
        _headers.update(headers)
        headers = _headers

        token = self.get_bearer_token()

        if self.logged_in:
            headers.update({
                'Authorization': 'Bearer %s' % token,
            })

        if etag:
            headers.update({
                'If-Match': etag,
            })

        if endpoint:
            url = endpoint + '/' + path
        else:
            url = self.endpoint + '/api' + path

        # Setting the parameter at all (even False) turns on admin mode
        if self.admin:
            params.update({'admin': self.admin})

        if params:
            self.logger.debug(
                "params={}".format(params)
            )

        if json:
            self.logger.debug(
                "json={}".format(json)
            )

        response = self.session.request(
            method,
            url,
            params=params,
            headers=headers,
            json=json
        )
        if response.status_code >= 500:
            raise PanoptesAPIException(
                'Received HTTP status code {} from API'.format(
                    response.status_code
                )
            )
        return response

    def json_request(
        self,
        method,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        response = self.http_request(
            method,
            path,
            params,
            headers,
            json,
            etag,
            endpoint
        )

        if (
            response.status_code == 204 or
            int(response.headers.get('Content-Length', -1)) == 0 or
            len(response.text) == 0
        ):
            json_response = None
        else:
            json_response = response.json()
            if 'errors' in json_response:
                raise PanoptesAPIException(', '.join(
                    map(lambda e: e.get('message', ''),
                        json_response['errors']
                       )
                ))
            elif 'error' in json_response:
                raise PanoptesAPIException(json_response['error'])

        return (json_response, response.headers.get('ETag'))

    def get_request(self, path, params={}, headers={}, endpoint=None):
        return self.http_request(
            'GET',
            path,
            params=params,
            headers=headers,
            endpoint=endpoint
        )

    def get(self, path, params={}, headers={}, endpoint=None):
        return self.json_request(
            'GET',
            path,
            params=params,
            headers=headers,
            endpoint=endpoint
        )

    def put_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.http_request(
            'PUT',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=None
        )

    def put(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.json_request(
            'PUT',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint
        )

    def post_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.http_request(
            'post',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint
        )

    def post(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.json_request(
            'POST',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint
        )

    def delete_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.http_request(
            'delete',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=None
        )

    def delete(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None
    ):
        return self.json_request(
            'DELETE',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint
        )

    def login(self, username=None, password=None):
        if not username:
            username = self.username
        else:
            self.username = username

        if not password:
            password = self.password
        else:
            self.password = password

        if not username or not password:
            return

        login_data = {
            'authenticity_token': self.get_csrf_token(),
            'user': {
                'login': username,
                'password': password,
                'remember_me': True,
            },
        }
        response = self.session.post(
            self.endpoint + '/users/sign_in',
            json=login_data,
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
        )
        if response.status_code != 200:
            raise PanoptesAPIException(
                response.json().get('error', 'Login failed')
            )
        self.logged_in = True
        return response

    def get_csrf_token(self):
        url = self.endpoint + '/users/sign_in'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        return self.session.get(url, headers=headers).headers['x-csrf-token']

    def get_bearer_token(self):
        if not self.valid_bearer_token():
            grant_type = 'password'

            if self.client_secret:
                grant_type = 'client_credentials'

            if not self.logged_in:
                if grant_type is 'password':
                    if not self.login():
                        return

            if (self.bearer_token and self.refresh_token):
                bearer_data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': self.client_id,
                }
            else:
                bearer_data = {
                    'grant_type': grant_type,
                    'client_id': self.client_id,
                }

            if grant_type == 'client_credentials':
                bearer_data['client_secret'] = self.client_secret
                bearer_data['url'] = self.redirect_url

            token_response = self.session.post(
                self.endpoint + '/oauth/token',
                bearer_data
            ).json()

            if 'errors' in token_response:
                raise PanoptesAPIException(token_response['errors'])

            self.bearer_token = token_response['access_token']
            if (self.bearer_token and grant_type == 'client_credentials'):
                self.logged_in = True
            if 'refresh_token' in token_response:
                self.refresh_token = token_response['refresh_token']
            else:
                self.refresh_token = None
            self.bearer_expires = (
                datetime.now()
                + timedelta(seconds=token_response['expires_in'])
            )
        return self.bearer_token

    def valid_bearer_token(self):
        # Return invalid if there is no token
        if not self.has_bearer_token():
            return False

        now = datetime.now()
        expires = self.bearer_expires
        # Buffer to allow time for requests
        # to fire without expiring in transit
        buffer_ = timedelta(minutes=2)

        # Add time to now --> pretend time is later
        # Effect of making token expire earlier
        return now + buffer_ <= expires

    def has_bearer_token(self):
        return self.bearer_token is not None

class PanoptesObject(object):
    """
    The base class of all Panoptes model classes. You should never need to
    create instances of this class, but the methods defined here are common to
    all the model subclasses.
    """

    RESERVED_ATTRIBUTES = (
        '_loaded',
        'etag',
        'links',
        'modified_attributes',
        'raw',
    )

    @classmethod
    def url(cls, *args):
        return '/'.join(['', cls._api_slug] + [str(a) for a in args if a])

    @classmethod
    def http_get(cls, path, params={}, headers={}):
        return Panoptes.client().get(
            cls.url(path),
            params,
            headers
        )

    @classmethod
    def http_post(cls, path, params={}, headers={}, json=None):
        return Panoptes.client().post(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def http_put(cls, path, params={}, headers={}, json=None):
        return Panoptes.client().put(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def http_delete(cls, path, params={}, headers={}, json=None):
        return Panoptes.client().delete(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def where(cls, **kwargs):
        """
        Returns a generator which yields instances matching the given query
        arguments.

        For example, this would yield all :py:class:`Project`s::

            Project.where()

        And this would yield all launch approved :py:class:`Project`s::

            Project.where(launch_approved=True)
        """

        _id = kwargs.pop('id', '')
        return cls.paginated_results(*cls.http_get(_id, params=kwargs))

    @classmethod
    def find(cls, _id):
        """
        Returns the individual instance with the given ID, if it exists. Raises
        :py:class:`PanoptesAPIException` if the object with that ID is not
        found.
        """

        if not _id:
            return None
        try:
            return cls.where(id=_id).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find {} with id='{}'".format(cls.__name__, _id)
            )

    @classmethod
    def paginated_results(cls, response, etag):
        return ResultPaginator(cls, response, etag)

    def __init__(self, raw={}, etag=None):
        self._loaded = False
        self.links = LinkResolver(self)

        if type(raw) == dict:
            self.set_raw(raw, etag)
        else:
            self.set_raw({}, loaded=False)
            self.raw['id'] = raw

    def __getattr__(self, name):
        try:
            if (
                name not in PanoptesObject.RESERVED_ATTRIBUTES
                and name is not 'id'
                and not self._loaded
            ):
                self.reload()
                return getattr(self, name)
            return self.raw[name]
        except KeyError:
            if name == 'id':
                return None
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__,
                name
            ))

    def __setattr__(self, name, value):
        if name in PanoptesObject.RESERVED_ATTRIBUTES:
            return super(PanoptesObject, self).__setattr__(name, value)

        if not self._loaded:
            self.reload()

        if name not in self.raw:
            return super(PanoptesObject, self).__setattr__(name, value)

        if name not in self._edit_attributes:
            raise ReadOnlyAttributeException(
                '{} is read-only'.format(name)
            )

        self.raw[name] = value
        self.modified_attributes.add(name)

    def __repr__(self):
        return '<{} {}>'.format(
            self.__class__.__name__,
            self.id
        )

    def set_raw(self, raw, etag=None, loaded=True):
        self.raw = {}
        self.raw.update(self._savable_dict(include_none=True))
        self.raw.update(raw)
        self.etag = etag
        self.modified_attributes = set()

        self._loaded = loaded

    def _savable_dict(
        self,
        attributes=None,
        modified_attributes=None,
        include_none=False,
    ):
        if not attributes:
            attributes = self._edit_attributes
        out = []
        for key in attributes:
            if type(key) == dict:
                for subkey, subattributes in key.items():
                    if (
                        subkey == 'links' and
                        hasattr(self, 'links') and
                        modified_attributes and
                        'links' in modified_attributes
                    ):
                        out.append(
                            (subkey, self.links._savable_dict(subattributes))
                        )
                    else:
                        out.append((subkey, self._savable_dict(
                            attributes=subattributes,
                            include_none=include_none
                        )))
            elif modified_attributes and key not in modified_attributes:
                continue
            else:
                value = self.raw.get(key)
                if value is not None or include_none:
                    out.append((key, value))
        return dict(out)

    def save(self):
        """
        Saves the object. If the object has not been saved before (i.e. it's
        new), then a new object is created. Otherwise, any changes are
        submitted to the API.
        """

        if not self.id:
            save_method = Panoptes.client().post
            force_reload = False
        else:
            if not self.modified_attributes:
                return
            if not self._loaded:
                self.reload()
            save_method = Panoptes.client().put
            force_reload = True

        response, response_etag = save_method(
            self.url(self.id),
            json={self._api_slug: self._savable_dict(
                modified_attributes=self.modified_attributes
            )},
            etag=self.etag
        )

        raw_resource_response = response[self._api_slug][0]
        self.set_raw(raw_resource_response, response_etag)

        if force_reload:
            self._loaded = False

        return response

    def reload(self):
        """
        Re-fetches the object from the API, discarding any local changes.
        Returns without doing anything if the object is new.
        """

        if not self.id:
            return
        reloaded_object = self.__class__.find(self.id)
        self.set_raw(
            reloaded_object.raw,
            reloaded_object.etag
        )

class ResultPaginator(object):
    def __init__(self, object_class, response, etag):
        if response is None:
            response = {}

        self.object_class = object_class
        self.set_page(response)
        self.etag = etag

    def __iter__(self):
        return self

    def __next__(self):
        if self.object_index >= self.object_count:
            if self.object_count and self.next_href:
                response, _ = Panoptes.client().get(self.next_href)
                self.set_page(response)
                return self.next()
            else:
                raise StopIteration

        i = self.object_index
        self.object_index += 1
        return self.object_class(self.object_list[i], etag=self.etag)
    next = __next__

    def set_page(self, response):
        self.meta = response.get('meta', {})
        self.meta = self.meta.get(self.object_class._api_slug, {})
        self.page = self.meta.get('page', 1)
        self.page_count = self.meta.get('page_count', 1)
        self.next_href = self.meta.get('next_href')
        self.object_list = response.get(self.object_class._api_slug, [])
        self.object_count = len(self.object_list)
        self.object_index = 0

class LinkResolver(object):
    types = {}

    @classmethod
    def register(cls, object_class, link_slug=None):
        if not link_slug:
            link_slug = object_class._link_slug
        cls.types[link_slug] = object_class

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, name):
        if not self.parent._loaded:
            self.parent.reload()

        linked_object = self.parent.raw['links'][name]
        object_class = LinkResolver.types.get(name)
        if (
            not object_class and
            type(linked_object == dict) and
            'type' in linked_object
        ):
            object_class = LinkResolver.types.get(linked_object['type'])


        if type(linked_object) == list:
            return [object_class(_id) for _id in linked_object]
        if type(linked_object) == dict and 'id' in linked_object:
            return object_class(linked_object['id'])
        else:
            return object_class(linked_object)

    def __setattr__(self, name, value):
        reserved_names = ('raw', 'parent')
        if name not in reserved_names and name in self.parent.raw['links']:
            if not self.parent._loaded:
                self.parent.reload()
            if isinstance(value, PanoptesObject):
                value = value.id
            self.parent.raw['links'][name] = value
            self.parent.modified_attributes.add('links')
        else:
            super(LinkResolver, self).__setattr__(name, value)

    def _savable_dict(self, edit_attributes):
        out = []
        for key, value in self.parent.raw['links'].items():
            if not key in edit_attributes:
                continue
            if type(key) == list:
               out.append((key, [ o.id for o in value ]))
            else:
                if value:
                    out.append((key, value))
        return dict(out)

class PanoptesAPIException(Exception):
    """
    Raised whenever the API returns an error. The exception will contain the
    raw error message from the API.
    """
    pass

class ReadOnlyAttributeException(Exception):
    """
    Raised if an attempt is made to modify an attribute of a
    :py:class:`PanoptesObject` which the API does not allow to be modified.
    """

    pass


class Talk(object):
    def __init__(self, endpoint='https://talk.zooniverse.org/'):
        self.endpoint = endpoint

    def http_get(self, *args, **kwargs):
        kwargs['endpoint'] = self.endpoint
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

    def get_data_request(self, section, kind):
        return self.http_get(
            'data_requests',
            params={
                'section': section,
                'kind': kind,
            }
        )

    def post_data_request(self, section, kind):
        return self.http_post(
            'data_requests',
            json={
                'data_requests': {
                    'section': section,
                    'kind': kind,
                }
            }
        )
