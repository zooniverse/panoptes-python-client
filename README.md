# panoptes-python-client

## Installation

Install latest release:

```
$ pip install panoptes-client
```

Install HEAD directly from GitHub:

```
$ pip install git+git://github.com/zooniverse/panoptes-python-client.git
```

## Usage Examples

Print all projects:

```python
from panoptes_client import Project

for project in Project.find():
    print project
```
