from __future__ import absolute_import, division, print_function
from builtins import str

import getpass
import logging
import os
import requests
import threading
import pkg_resources

from datetime import datetime, timedelta
from redo import retrier

import six

from panoptes_client.utils import isiterable, batchable

HTTP_RETRY_LIMIT = 5
RETRY_BACKOFF_INTERVAL = 5

if os.environ.get('PANOPTES_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()


class Panoptes(object):
    """
    The low-level Panoptes HTTP client class. Use this class to log into the
    API. In most cases you can just call :py:meth:`.Panoptes.connect` once and
    all subsequent API requests will be authenticated.

    If you want to configure multiple clients, e.g. to perform operations as
    multiple users, you should initialise the client as a context manager,
    using the `with` statement instead of using :py:meth:`.Panoptes.connect`.
    In this example, we modify a project by authenticating as the project
    owner, then log in as a regular user to add a subject to a collection,
    then switch back to the project owner's account to retire some subjects::

        owner_client = Panoptes(username='example-project-owner', password='')

        with owner_client:
            project = Project(1234)
            project.display_name = 'New name'
            project.save()

        with Panoptes(username='example-user', password=''):
            Collection(1234).add(Subject(1234))

        with owner_client:
            Workflow(1234).retire_subjects([1234, 5678, 9012])

    Using the `with` statement in this way ensures it is clear which user will
    be used for each action.
    """

    _http_headers = {
        'default': {
            'Accept': 'application/vnd.api+json; version=1',
            'User-Agent': 'panoptes-python-client/version=' + pkg_resources.require('panoptes_client')[0].version
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

    _local = threading.local()

    @classmethod
    def connect(cls, *args, **kwargs):
        """
        connect(username=None, password=None, endpoint=None, admin=False)

        Configures the Panoptes client for use.

        Note that there is no need to call this unless you need to pass one or
        more of the below arguments.  By default, the client will connect to
        the public Zooniverse.org API as an anonymous user.

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
        cls._local.panoptes_client = cls(*args, **kwargs)
        cls._local.panoptes_client.login()
        return cls._local.panoptes_client

    @classmethod
    def client(cls, *args, **kwargs):
        local_client = getattr(cls._local, "panoptes_client", None)
        if not local_client:
            return cls(*args, **kwargs)
        return local_client

    def __init__(
        self,
        endpoint=None,
        client_id=None,
        client_secret=None,
        redirect_url=None,
        username=None,
        password=None,
        login=None,
        admin=False
    ):
        self.session = requests.session()

        self.endpoint = endpoint or os.environ.get(
            'PANOPTES_ENDPOINT',
            'https://www.zooniverse.org'
        )
        self.logged_in = False
        self.username = None
        self.password = None
        self._auth(login, username, password)
        self.login()

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

        self.logger = logging.getLogger('panoptes_client')

    def __enter__(self):
        self._local.previous_client = getattr(
            self._local,
            'panoptes_client',
            None,
        )
        self._local.panoptes_client = self
        return self

    def __exit__(self, *exc):
        self._local.panoptes_client = self._local.previous_client

    def http_request(
        self,
        method,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
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

        if retry:
            retry_attempts = HTTP_RETRY_LIMIT
        else:
            retry_attempts = 1

        for _ in retrier(
            attempts=retry_attempts,
            sleeptime=RETRY_BACKOFF_INTERVAL,
        ):
            response = self.session.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json,
            )
            if response.status_code < 500:
                break
        else:
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
        endpoint=None,
        retry=False,
    ):
        response = self.http_request(
            method=method,
            path=path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint,
            retry=retry,
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

    def get_request(
        self,
        path,
        params={},
        headers={},
        endpoint=None,
        retry=False,
    ):
        return self.http_request(
            'GET',
            path,
            params=params,
            headers=headers,
            endpoint=endpoint,
            retry=retry,
        )

    def get(
        self,
        path,
        params={},
        headers={},
        endpoint=None,
        retry=False,
    ):
        return self.json_request(
            'GET',
            path,
            params=params,
            headers=headers,
            endpoint=endpoint,
            retry=retry,
        )

    def put_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.http_request(
            'PUT',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=None,
            retry=retry,
        )

    def put(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.json_request(
            'PUT',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint,
            retry=retry,
        )

    def post_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.http_request(
            'post',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint,
            retry=retry,
        )

    def post(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.json_request(
            'POST',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint,
            retry=retry,
        )

    def delete_request(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.http_request(
            'delete',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=None,
            retry=retry,
        )

    def delete(
        self,
        path,
        params={},
        headers={},
        json=None,
        etag=None,
        endpoint=None,
        retry=False,
    ):
        return self.json_request(
            'DELETE',
            path,
            params=params,
            headers=headers,
            json=json,
            etag=etag,
            endpoint=endpoint,
            retry=retry,
        )

    def _auth(self, auth_type, username, password):
        if username is None or password is None:
            if auth_type == 'interactive':
                username, password = self.interactive_login()

            elif auth_type == 'keyring':
                # Get credentials from python keyring
                pass

            else:
                username = os.environ.get('PANOPTES_USERNAME')
                password = os.environ.get('PANOPTES_PASSWORD')

        self.username = username
        self.password = password


    def login(self, username=None, password=None):
        if self.logged_in:
            return

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

    def interactive_login(self):
        print('Enter your Zooniverse credentials...')
        username = input('Username: ')
        password = getpass.getpass()

        return username, password

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
                if grant_type == 'password':
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

    `PanoptesObject`s support lazy loading of attributes, where data is loaded
    from the API only when it is first accessed. You can do this by passing an
    object ID to the contructor::

        project = Project(1234)
        print(project.display_name)

    This will not make any HTTP requests until the `print` statement.
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
    def http_get(cls, path, params={}, headers={}, retry=True, **kwargs):
        return Panoptes.client().get(
            cls.url(path),
            params,
            headers,
            retry=retry,
            **kwargs
        )

    @classmethod
    def http_post(cls, path, params={}, headers={}, json=None, **kwargs):
        return Panoptes.client().post(
            cls.url(path),
            params,
            headers,
            json,
            **kwargs
        )

    @classmethod
    def http_put(cls, path, params={}, headers={}, json=None, **kwargs):
        return Panoptes.client().put(
            cls.url(path),
            params,
            headers,
            json,
            **kwargs
        )

    @classmethod
    def http_delete(cls, path, params={}, headers={}, json=None, **kwargs):
        return Panoptes.client().delete(
            cls.url(path),
            params,
            headers,
            json,
            **kwargs
        )

    @classmethod
    def where(cls, **kwargs):
        """
        Returns a generator which yields instances matching the given query
        arguments.

        For example, this would yield all :py:class:`.Project`::

            Project.where()

        And this would yield all launch approved :py:class:`.Project`::

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
            return next(cls.where(id=_id))
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
                and name != 'id'
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
                        links_out = (subkey, self._savable_dict(
                            attributes=subattributes,
                            include_none=include_none
                        ))
                        if links_out[1]:
                            out.append(links_out)
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

    def delete(self):
        """
        Deletes the object. Returns without doing anything if the object is
        new.
        """

        if not self.id:
            return
        if not self._loaded:
            self.reload()
        return self.http_delete(self.id, etag=self.etag)

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
                return next(self)
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
    readonly = set()

    @classmethod
    def register(cls, object_class, link_slug=None, readonly=False):
        if not link_slug:
            link_slug = object_class._link_slug
        cls.types[link_slug] = object_class
        if readonly:
            cls.readonly.add(link_slug)

    @classmethod
    def isreadonly(cls, link_slug):
        return link_slug in cls.readonly

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

        if isinstance(linked_object, LinkCollection):
            return linked_object
        if isinstance(linked_object, list):
            lc = getattr(self.parent, '_link_collection', LinkCollection)(
                object_class,
                name,
                self.parent,
                linked_object
            )
            self.parent.raw['links'][name] = lc
            return lc
        if isinstance(linked_object, dict) and 'id' in linked_object:
            return object_class(linked_object['id'])
        else:
            return object_class(linked_object)

    def __setattr__(self, name, value):
        reserved_names = ('raw', 'parent')
        if name not in reserved_names and name not in dir(self):
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
            if isiterable(value):
                out.append((key, [getattr(o, 'id', o) for o in value]))
            else:
                if value:
                    out.append((key, value))
        return dict(out)


class LinkCollection(object):
    """
    A collection of :py:class:`.PanoptesObject` of one class which are linked
    to a parent :py:class:`.PanoptesObject`.

    Allows indexing, iteration, and membership testing::

        project = Project(1234)

        print(project.links.workflows[2].display_name)

        for workflow in project.links.workflows:
            print(workflow.id)

        if Workflow(5678) in project.links.workflows:
            print('Workflow found')

        # Integers, strings, and PanoptesObjects are all OK
        if 9012 not in project.links.workflows:
            print('Workflow not found')
    """
    def __init__(self, cls, slug, parent, linked_objects):
        self._linked_object_ids = list(linked_objects)
        self._cls = cls
        self._slug = slug
        self._parent = parent
        self.readonly = LinkResolver.isreadonly(slug)

    def __contains__(self, obj):
        if isinstance(obj, self._cls):
            obj_id = str(obj.id)
        else:
            obj_id = str(obj)

        return obj_id in self._linked_object_ids

    def __getitem__(self, i):
        return self._cls(self._linked_object_ids[i])

    def __iter__(self):
        for obj_id in self._linked_object_ids:
            yield self._cls(obj_id)

    def __repr__(self):
        return "[{}]".format(", ".join([
            "<{} {}>".format(self._cls.__name__, obj)
            for obj in self._linked_object_ids
        ]))

    @batchable
    def add(self, objs):
        """
        Adds the given `objs` to this `LinkCollection`.

        - **objs** can be a list of :py:class:`.PanoptesObject` instances, a
          list of object IDs, a single :py:class:`.PanoptesObject` instance, or
          a single object ID.

        Examples::

            organization.links.projects.add(1234)
            organization.links.projects.add(Project(1234))
            workflow.links.subject_sets.add([1,2,3,4])
            workflow.links.subject_sets.add([Project(12), Project(34)])
        """

        if self.readonly:
            raise NotImplementedError(
                '{} links can\'t be modified'.format(self._slug)
            )

        if not self._parent.id:
            raise ObjectNotSavedException(
                "Links can not be modified before the object has been saved."
            )

        _objs = [obj for obj in self._build_obj_list(objs) if obj not in self]
        if not _objs:
            return

        self._parent.http_post(
            '{}/links/{}'.format(self._parent.id, self._slug),
            json={self._slug: _objs},
            retry=True,
        )
        self._linked_object_ids.extend(_objs)

    @batchable
    def remove(self, objs):
        """
        Removes the given `objs` from this `LinkCollection`.

        - **objs** can be a list of :py:class:`.PanoptesObject` instances, a
          list of object IDs, a single :py:class:`.PanoptesObject` instance, or
          a single object ID.

        Examples::

            organization.links.projects.remove(1234)
            organization.links.projects.remove(Project(1234))
            workflow.links.subject_sets.remove([1,2,3,4])
            workflow.links.subject_sets.remove([Project(12), Project(34)])
        """

        if self.readonly:
            raise NotImplementedError(
                '{} links can\'t be modified'.format(self._slug)
            )

        if not self._parent.id:
            raise ObjectNotSavedException(
                "Links can not be modified before the object has been saved."
            )

        _objs = [obj for obj in self._build_obj_list(objs) if obj in self]
        if not _objs:
            return

        _obj_ids = ",".join(_objs)
        self._parent.http_delete(
            '{}/links/{}/{}'.format(self._parent.id, self._slug, _obj_ids),
            retry=True,
        )
        self._linked_object_ids = [
            obj for obj in self._linked_object_ids if obj not in _objs
        ]

    def _build_obj_list(self, objs):
        _objs = []
        for obj in objs:
            if not (
                isinstance(obj, self._cls)
                or isinstance(obj, (int, six.string_types,))
            ):
                raise TypeError

            if isinstance(obj, self._cls):
                _obj_id = str(obj.id)
            else:
                _obj_id = str(obj)

            _objs.append(_obj_id)

        return _objs


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


class ObjectNotSavedException(Exception):
    """
    Raised if an attempt is made to perform an operation on an unsaved
    :py:class:`PanoptesObject` which requires the object to be saved first.
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
