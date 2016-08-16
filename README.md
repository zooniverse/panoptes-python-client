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

for project in Project.where():
    print project.title
```

Find a project by slug and print all its workflow names:

```python
from panoptes_client import Project

project = Project.find(slug='zooniverse/example')
for workflow in project.links.workflows:
    print workflow.display_name
```

Create a project:

```python
from panoptes_client import Project, Panoptes
Panoptes.connect(username='example', password='example')
p = Project()
p.display_name='test project'
p.description='a test project'
p.primary_language='en'
p.private=True
p.save()
```

Create a subject set and upload a new subject to it:

```python
from panoptes_client import SubjectSet, Subject, Project, Panoptes

Panoptes.connect(username='example', password='example')

project = Project.find(slug='zooniverse/example')

subject_set = SubjectSet()
subject_set.links.project = project
subject_set.display_name = 'My new subject set'
subject_set.save()

subject = Subject()
subject.links.project = project
subject.add_location('/path/to/local/image.jpg')
# You can set whatever metadata you want, or none at all
subject.metadata['image_id'] = 1234
subject.metadata['image_title'] = 'My image'
subject.save()

# SubjectSet.add() can take a list of Subjects, or just one.
subject_set.add(subject)
```

Project owners with client credentials can update their users' project settings (workflow_id only):

```python
from panoptes_client import Panoptes, User, Subject, ProjectPreferences
Panoptes.connect(client_id="example",client_secret="example")
user = User.find("1234")
project = Project.find("1234")
project_prefs = ProjectPreferences.find(user=user,project=project)
settings = {"workflow_id": "1234"}
pp.update_settings(settings)
```
