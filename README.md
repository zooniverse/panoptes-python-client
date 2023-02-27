# Panoptes Client

This package is the Python SDK for
[Panoptes](https://github.com/zooniverse/Panoptes), the platform behind the
[Zooniverse](https://www.zooniverse.org/). This module is intended to allow
programmatic management of projects, providing high level access to the API for
common project management tasks.

[Full documentation is available at Read the
Docs](http://panoptes-python-client.readthedocs.io/).

## Installation

Install latest stable release:

```
$ pip install panoptes-client
```

Or for development or testing, you can install the development version directly
from GitHub:

```
$ pip install -U git+https://github.com/zooniverse/panoptes-python-client.git
```

Upgrade an existing installation:

```
$ pip install -U panoptes-client
```

The Panoptes Client is supported on all versions of Python 2 and 3, from Python
2.7 onwards.

## Usage Examples

Create a project:

```python
from panoptes_client import Panoptes, Project

Panoptes.connect(username='example', password='example')

new_project = Project()
new_project.display_name = 'My new project'
new_project.description = 'A great new project!'
new_project.primary_language = 'en'
new_project.private = True
new_project.save()
```

See the documentation for [additional
examples](http://panoptes-python-client.readthedocs.io/en/latest/user_guide.html#usage-examples).

## Contributing

We welcome bug reports and code contributions. Please see
[CONTRIBUTING.md](https://github.com/zooniverse/panoptes-python-client/blob/master/CONTRIBUTING.md)
for information about how you can get involved.

### Running the Tests

You can run the tests with Docker. This will run them under Python 3 and Python
2:

```
docker-compose build tests && docker-compose run tests
docker-compose build tests2 && docker-compose run tests2
```

Or you can run them directly in Python with:

```python
python -m unittest discover
```
