import requests

from datetime import datetime, timedelta

class Panoptes(object):
    _client = None

    _default_headers = {
        'Accept': 'application/vnd.api+json; version=1',
    }
    _default_get_headers = {}
    _default_put_headers = {}
    _default_post_headers = {}
    _default_put_post_headers = {
        'Content-Type': 'application/json',
    }

    _endpoint_client_ids = {
        'default': (
            'f79cf5ea821bb161d8cbb52d061ab9a2321d7cb169007003af66b43f7b79ce2a'
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
        endpoint='https://panoptes.zooniverse.org',
        client_id=None,
        username=None,
        password=None
    ):
        Panoptes._client = self

        self.endpoint = endpoint
        self.username = username
        self.password = password

        if client_id:
            self.client_id = client_id
        else:
            self.client_id = self._endpoint_client_ids.get(
                self.endpoint,
                self._endpoint_client_ids['default']
            )

        self.logged_in = False
        self.bearer_token = None

        self.session = requests.session()

    def _headers_for_all(self):
        headers = self._default_headers.copy()
        token = self.get_bearer_token()
        if self.logged_in:
            headers.update({
                'Authorization': 'Bearer %s' % token,
            })
        return headers

    def _headers_for_get(self):
        headers = self._headers_for_all()
        headers.update(self._default_get_headers)
        return headers

    def _headers_for_put(self):
        headers = self._headers_for_all()
        headers.update(self._default_put_post_headers)
        headers.update(self._default_get_headers)
        return headers

    def _headers_for_post(self):
        headers = self._headers_for_all()
        headers.update(self._default_headers)
        headers.update(self._default_put_post_headers)
        headers.update(self._default_get_headers)
        return headers

    def get_request(self, path, params={}, headers={}):
        _headers = self._headers_for_get().copy()
        _headers.update(headers)
        headers = _headers
        url = self.endpoint + '/api' + path
        return self.session.get(url, params=params,  headers=headers)

    def get(self, path, params={}, headers={}):
        return self.get_request(path, params, headers).json()

    def put_request(self, path, params={}, headers={}):
        _headers = self._headers_for_put().copy()
        _headers.update(headers)
        headers = _headers
        url = self.endpoint + '/api' + path
        return self.session.put(url, params=params,  headers=headers)

    def put(self, path, params={}, headers={}):
        return self.put_request(path, params, headers).json()

    def post_request(self, path, params={}, headers={}, json={}):
        _headers = self._headers_for_post().copy()
        _headers.update(headers)
        headers = _headers
        url = self.endpoint + '/api' + path
        return self.session.post(
            url,
            params=params,
            headers=headers,
            json=json
        )

    def post(self, path, params={}, headers={}, json={}):
        return self.post_request(path, params, headers, json).json()

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
        if not self.bearer_token or self.bearer_expires > datetime.now():
            if not self.logged_in:
                if not self.login():
                    return
            if self.bearer_token:
                bearer_data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': self.client_id,
                }
            else:
                bearer_data = {
                    'grant_type': 'password',
                    'client_id': self.client_id,
                }
            token_response = self.session.post(
                self.endpoint + '/oauth/token',
                bearer_data
            ).json()
            self.bearer_token = token_response['access_token']
            self.refresh_token = token_response['refresh_token']
            self.bearer_expires = (
                datetime.now()
                + timedelta(seconds=token_response['expires_in'])
            )
        return self.bearer_token

class PanoptesObject(object):
    raw = {}

    @classmethod
    def url(cls, *args):
        return '/'.join(['', cls.slug] + list(args))

    @classmethod
    def get(cls, path, params={}, headers={}):
        return Panoptes.client().get(
            cls.url(path),
            params,
            headers
        )

    def __init__(self, raw=None, client=None):
        if not client:
            self.client = Panoptes.client()
        else:
            self.client = client
        if raw:
            self.raw = raw

    def __getattr__(self, name):
        try:
            return self.raw[name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__,
                name
            ))
