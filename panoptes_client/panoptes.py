import requests
import os

from datetime import datetime, timedelta

class Panoptes(object):
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
            'f79cf5ea821bb161d8cbb52d061ab9a2321d7cb169007003af66b43f7b79ce2a'
        ),
        'https://panoptes-staging.zooniverse.org': (
            '535759b966935c297be11913acee7a9ca17c025f9f15520e7504728e71110a27'
        ),
    }

    @classmethod
    def connect(cls, *args, **kwargs):
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
            'https://panoptes.zooniverse.org'
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

    def http_request(
        self,
        method,
        path,
        params={},
        headers={},
        json={},
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
        json={},
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
        json={},
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
        json={},
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
        json={},
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
        json={},
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
        json={},
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
        json={},
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
        if not self.bearer_token or self.bearer_expires < datetime.now():
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

class PanoptesObject(object):
    @classmethod
    def url(cls, *args):
        return '/'.join(['', cls._api_slug] + [ unicode(a) for a in args if a ])

    @classmethod
    def http_get(cls, path, params={}, headers={}):
        return Panoptes.client().get(
            cls.url(path),
            params,
            headers
        )

    @classmethod
    def http_post(cls, path, params={}, headers={}, json={}):
        return Panoptes.client().post(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def http_put(cls, path, params={}, headers={}, json={}):
        return Panoptes.client().put(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def http_delete(cls, path, params={}, headers={}, json={}):
        return Panoptes.client().delete(
            cls.url(path),
            params,
            headers,
            json
        )

    @classmethod
    def where(cls, **kwargs):
        _id = kwargs.pop('id', '')
        return cls.paginated_results(*cls.http_get(_id, params=kwargs))

    @classmethod
    def find(cls, _id):
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
        self.set_raw(raw, etag)

    def __getattr__(self, name):
        try:
            return self.raw[name]
        except KeyError:
            if name == 'id':
                return None
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__,
                name
            ))

    def __setattr__(self, name, value):
        reserved_names = ('raw', 'links')
        if name not in reserved_names and name in self.raw:
            if name not in self._edit_attributes:
                raise ReadOnlyAttributeException(
                    '{} is read-only'.format(name)
                )
            self.raw[name] = value
            self.modified_attributes.add(name)
        else:
            super(PanoptesObject, self).__setattr__(name, value)

    def __repr__(self):
        return '<{} {}>'.format(
            self.__class__.__name__,
            self.id
        )

    def set_raw(self, raw, etag=None):
        self.raw = {}
        self.raw.update(self._savable_dict(include_none=True))
        self.raw.update(raw)
        self.etag = etag
        self.modified_attributes = set()

        if 'links' in self.raw:
            self.links = LinkResolver(self.raw['links'], self)

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
        if not self.id:
            save_method = Panoptes.client().post
        else:
            save_method = Panoptes.client().put

        response, _ = save_method(
            self.url(self.id),
            json={self._api_slug: self._savable_dict(
                modified_attributes=self.modified_attributes
            )},
            etag=self.etag
        )
        self.raw['id'] = response[self._api_slug][0]['id']
        self.reload()
        return response

    def reload(self):
        reloaded_project = self.__class__.find(self.id)
        self.set_raw(
            reloaded_project.raw,
            reloaded_project.etag
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

    def next(self):
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

    def __init__(self, raw, parent):
        self.raw = raw
        self.parent = parent

    def __getattr__(self, name):
        object_class = LinkResolver.types.get(name)
        linked_object = self.raw[name]
        if type(linked_object) == list:
            return map(lambda o: object_class.find(o), linked_object)
        if type(linked_object) == dict and 'id' in linked_object:
            return object_class.find(linked_object['id'])
        else:
            return object_class.find(linked_object)

    def __setattr__(self, name, value):
        reserved_names = ('raw', 'parent')
        if name not in reserved_names and name in self.raw:
            if isinstance(value, PanoptesObject):
                value = value.id
            self.raw[name] = value
            self.parent.modified_attributes.add('links')
        else:
            super(LinkResolver, self).__setattr__(name, value)

    def _savable_dict(self, edit_attributes):
        out = []
        for key, value in self.raw.items():
            if not key in edit_attributes:
                continue
            if type(key) == list:
               out.append((key, [ o.id for o in value ]))
            else:
                if value:
                    out.append((key, value))
        return dict(out)

class PanoptesAPIException(Exception):
    pass

class ReadOnlyAttributeException(Exception):
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
