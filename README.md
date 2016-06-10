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

Print all project titles:

```python
from panoptes_client import Project

for project in Project.find():
    print project.title
```

Find a project by slug and print all its workflow names:

```python
from panoptes_client import Project

project = Project.find(slug='zooniverse/example').next()
for workflow in project.links.workflows:
    print workflow.display_name
```
