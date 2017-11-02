User Guide
==========

Introduction
------------

The Panoptes Client provides high level access to the HTTP API for common
project management tasks. The client module provides a set of classes which act
as an object-relational mapping (ORM) layer on top of the API, allowing you to
perform tasks such as creating/uploading subjects, retiring subjects, and
downloading data exports without having to concern yourself with the low level
detail of how the API functions.

Most of the classes you'll need can be imported directly from the
``panoptes_client`` package; see the :doc:`module reference </panoptes_client>`
for a complete list.

Of special note is the :py:class:`.Panoptes` class which provides the
:py:meth:`.Panoptes.connect` method. This method must be called to log into the
API before you can perform any privileged, project owner-specific actions
(though some things, such as listing public projects or available workflows,
can be done anonymously, without logging in).

Most of the classes you'll be using are subclasses of the abstract
:py:class:`.PanoptesObject` class. Any references in this documentation to
"Panoptes object classes" or "model classes" refer to these subclasses. You
should familiarise yourself with the methods that Panoptes object classes all
have, in particular :py:meth:`.PanoptesObject.save` and
:py:meth:`.PanoptesObject.where`.

Installation
------------

Install latest stable release::

    $ pip install panoptes-client

Or for development or testing, you can install the development version directly
from GitHub::

    $ pip install -U git+git://github.com/zooniverse/panoptes-python-client.git

Upgrade an existing installation::

    $ pip install -U panoptes-client

Uploading non-image media types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to upload subjects with non-image media (e.g. audio or video),
you will need to make sure you have the ``libmagic`` library installed. If you
don't already have ``libmagic``, please see the `dependency information for
python-magic <https://github.com/ahupp/python-magic#dependencies>`_ for more
details.

Usage Examples
--------------

Tutorial: Creating a new project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the client installed, you can import the modules you need from the
``panoptes_client`` package. For this tutorial, we're going to log into the
Panoptes API, create a project, create a subject set, and finally create some
subjects to go in the new set. Let's start by importing all the classes we'll
need for that::

    from panoptes_client import Panoptes, Project, SubjectSet, Subject

Now that we've imported all that, we can use the :py:meth:`.Panoptes.connect`
method to log in::

    Panoptes.connect(username='example', password='example')

Next we will create our new project. All we need to do is instantiate a new
instance of :py:class:`.Project`, set some required attributes, and then save
it, like so::

    tutorial_project = Project()

    tutorial_project.display_name = 'Tutorial Project'
    tutorial_project.description = 'My first project created in Python'
    tutorial_project.primary_language = 'en'
    tutorial_project.private = True

    tutorial_project.save()


Now if you log into the `Zooniverse project builder
<https://www.zooniverse.org/lab>`_ you should see the new project listed there.
Next we will create a subject set in the same way::

    subject_set = SubjectSet()

    subject_set.links.project = tutorial_project
    subject_set.display_name = 'Tutorial subject set'

    subject_set.save()

Here you'll notice we set the ``subject_set.links.project`` attribute. ``links``
is a special attribute that handles connecting related Panoptes objects to each
other. You can directly assign a Panoptes object instance, as above, or you can
assign an object's ID number if you have it. As well as assigning objects, you
can use ``links`` to access related objects. Now that we've created our new
subject set, we will also see a link to it on ``tutorial_project`` if we reload
it::

    tutorial_project.reload()
    print(tutorial_project.links.subject_sets)

This would output something like this::

    [<SubjectSet 1234>]

Showing a list of the linked subject sets (containing only our new set in this
case). Here ``1234`` is the internal ID number of the subject set (also
accessible as ``subject_set.id``), so the exact result you get will be slightly
different.

Now that we have a subject set, let's create some subjects and add them to it.
For this tutorial, we'll assume you have a :py:class:`dict` containing filenames
and subject metadata. In reality you might load this from a CSV file, or query a
database, or generate it in any number of different ways, but this would be
outside the scope of this tutorial::

    subject_metadata = {
        '/Users/me/file1.png': {
            'subject_reference': 1,
            'date': '2017-01-01',
        },
        '/Users/me/file2.png': {
            'subject_reference': 2,
            'date': '2017-01-02',
        },
        '/Users/me/file3.png': {
            'subject_reference': 3,
            'date': '2017-01-03',
        },
    }

Now we create a :py:class:`.Subject` instance for each one::

    new_subjects = []

    for filename, metadata in subject_metadata.items():
        subject = Subject()

        subject.links.project = tutorial_project
        subject.add_location(filename)

        subject.metadata.update(metadata)

        subject.save()
        new_subjects.append(subject)

Saving the subject will create the subject in Panoptes and then upload the
image file. The :py:meth:`.Subject.add_location` method prepares files to be
uploaded. You can give it a string, as above, to point to a path on the local
filesystem, or you can give it an open :py:class:`file` object, or a
:py:class:`dict` for remote URLs. See the :py:meth:`.Subject.add_location`
documentation for examples.


Note that by default the ``metadata`` attribute is an empty :py:class:`dict`,
so in this example we just call :py:meth:`dict.update()` to merge it with our
existing metadata. You can also set individual keys as normal::

    subject.metadata['my_metadata'] = 'abcd'

Or you can leave it empty if you don't need to set anything.

All that's left to do now is to link our new subjects to our new subject set.
That can be done with the :py:meth:`.SubjectSet.add` method::

    subject_set.add(new_subjects)

That takes the list of subjects and links them all in one go. This is the
preferred way of doing it if you have several subjects to link (because it's
faster than making several separate calls), but you can also link subjects one
at a time if you need to::

    subject_set.add(subject1)
    subject_set.add(subject2)

And that's all there is to it! Your new subjects are now linked to the new
subject set.

Other examples
~~~~~~~~~~~~~~

Print all project titles::

    for project in Project.where():
        print(project.title)

Find a project by slug and print all its workflow names::

    project = Project.find(slug='zooniverse/example')
    for workflow in project.links.workflows:
        print(workflow.display_name)

List the subjects in a subject_set::

    subject_set = SubjectSet.find(1234)
    for subject in subject_set.subjects:
        print(subject.id)

Add subject set to 1st workflow in project::

    workflow = project.links.workflows[0]
    workflow.add_subject_sets(subject_set)

Project owners with client credentials can update their users' project settings
(workflow_id only)::

    Panoptes.connect(client_id="example", client_secret="example")

    user = User.find("1234")
    project = Project.find("1234")
    new_settings = {"workflow_id": "1234"}

    ProjectPreferences.save_settings(
        project=project,
        user=user,
        settings=new_settings,
    )

Alternatively, the project ID and user ID can be passed in directly if they are
already known::

    ProjectPreferences.save_settings(
        project=project_id,
        user=user_id,
        settings=new_settings,
    )
