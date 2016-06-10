import requests

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

    def http_request(self, method, path, params={}, headers={}, json={}):
        _headers = self._http_headers['default'].copy()
        _headers.update(self._http_headers[method])
        _headers.update(headers)
        headers = _headers
        url = self.endpoint + '/api' + path
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

    def json_request(self, method, path, params={}, headers={}, json={}):
        json_response = self.http_request(method, path, params, headers).json()
        if 'errors' in json_response:
            raise PanoptesAPIException(', '.join(
                map(lambda e: e.get('message', ''),
                    json_response['errors']
                   )
            ))
        return json_response

    def get_request(self, path, params={}, headers={}):
        return self.http_request('GET', path, params, headers)

    def get(self, path, params={}, headers={}):
        return self.json_request('GET', path, params, headers)

    def put_request(self, path, params={}, headers={}):
        return self.http_request('PUT', path, params,  headers)

    def put(self, path, params={}, headers={}):
        return self.json_request('PUT', path, params, headers)

    def post_request(self, path, params={}, headers={}, json={}):
        return self.http_request(
            'post',
            path,
            params=params,
            headers=headers,
            json=json
        )

    def post(self, path, params={}, headers={}, json={}):
        return self.json_request('POST', path, params, headers, json)

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
        return '/'.join(['', cls._api_slug] + map(unicode, args))

    @classmethod
    def get(cls, path, params={}, headers={}):
        return Panoptes.client().get(
            cls.url(path),
            params,
            headers
        )

    @classmethod
    def paginated_results(cls, response):
        return PanoptesResultPaginator(cls, response)

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

class PanoptesResultPaginator(object):
    def __init__(self, object_class, response):
        self.object_class = object_class
        self.set_page(response)

    def __iter__(self):
        return self

    def next(self):
        if self.object_index >= self.object_count:
            if self.next_href:
                response = Panoptes.client().get(self.next_href)
                self.set_page(response)
            else:
                raise StopIteration

        i = self.object_index
        self.object_index += 1
        return self.object_class(self.object_list[i])

    def set_page(self, response):
        self.meta = response.get('meta', {})
        self.meta = self.meta.get(self.object_class._api_slug, {})
        self.page = self.meta.get('page', 1)
        self.page_count = self.meta.get('page_count', 1)
        self.next_href = self.meta.get('next_href')
        self.object_list = response.get(self.object_class._api_slug, [])
        self.object_count = len(self.object_list)
        self.object_index = 0

class PanoptesAPIException(Exception):
    pass
