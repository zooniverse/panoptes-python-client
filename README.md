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

# SubjectSet.add() can take a list of Subjects
subject_set.add([subject1, subject2, subject3])
# or just one at a time (but this is slower than doing several together)
subject_set.add(subject1)
subject_set.add(subject2)

# add subject set to 1st workflow in project
workflow = project.links.workflows[0]
workflow.add_subject_sets([subject_set])
```

List the subjects in a subject_set:

```python
subject_set=SubjectSet.find(1234)
for subject in subject_set.subjects:
    print("%s," % (subject.id))
```

Project owners with client credentials can update their users' project settings (workflow_id only):

```python
from panoptes_client import Panoptes, User, Subject, ProjectPreferences
Panoptes.connect(client_id="example",client_secret="example")
user = User.find("1234")
project = Project.find("1234")
new_settings = {"workflow_id": "1234"}
ProjectPreferences.save_settings(project=project, user=user, settings=new_settings)
```
Alternatively, the project id and user id can be passed in directly if they are already known:

 `ProjectPreferences.save_settings(project=project_id, user=user_id, settings=new_settings)`
