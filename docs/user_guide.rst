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

You might also want to refer to the `Panoptes API documentation
<https://panoptes.docs.apiary.io/>`_ as this lists the full options and allowed
values for many of the methods in this module -- many method arguments are
simply passed to the API as-is, with the API performing server-side validation.
The API documentation also lists the full attributes for each class; these are
not included in this documentation.

Installation
------------

Install latest stable release::

    $ pip install panoptes-client

Or for development or testing, you can install the development version directly
from GitHub::

    $ pip install -U git+https://github.com/zooniverse/panoptes-python-client.git

Upgrade an existing installation::

    $ pip install -U panoptes-client

The Panoptes Client is supported on all versions of Python 2 and 3, from Python
2.7 onwards.

Uploading non-image media types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to upload subjects with non-image media (e.g. audio or video),
it is desirable to have the ``libmagic`` library installed for type detection.
If you don't already have ``libmagic``, please see the `dependency information 
for python-magic <https://github.com/ahupp/python-magic#installation>`_ for
more details.

If `libmagic` is not installed, assignment of MIME types (e.g., image/jpeg,
video/mp4, text/plain, application/json, etc) will be based on file extensions.
Be aware that if file names and extension aren't accurate, this could lead to
issues when the media is loaded.

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

Tutorial: Adding a Workflow to Caesar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For this tutorial, we will connect to Caesar and add workflow to Caesar in 2 ways (via Caesar or via Workflow). We start by importing all the classes we'll need::

    from panoptes_client import Panoptes, Workflow, Caesar

Now that we've imported all that, we can use the :py:meth:`.Panoptes.connect`
method to log in (see above tutorial).

Next we can instantiate an instance of :py:class`.Caesar`::

    caesar = Caesar()

Note that the token from coming from :py:meth:`.Panoptes.connect` will also get us connected to Caesar.

We can add workflow to Caesar using this instace of :py:class`.Caesar`, assuming you have a `workflow_id` handy::

    caesar.save_workflow(1234)

Another way we can do this is via :py:class`.Workflow`. We can do this by first instantiating an instance of :py:class`.Workflow` with provided `workflow_id`::

    workflow = Workflow(1234)

We can then add this workflow to Caesar::

    workflow.save_to_caesar()



Tutorial: Retiring and Unretiring Subjects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For this tutorial, we're going to retire and unretire subjects in a given workflow. We start by importing all the classes we'll need::

    from panoptes_client import Panoptes, Workflow, Subject, SubjectSet

Now that we've imported all that, we can use the :py:meth:`.Panoptes.connect`
method to log in (see above tutorial)

Next we can instantiate an instance of :py:class`.Workflow`, assuming you have a `workflow_id` handy::

    workflow = Workflow('1234')

We can retire subjects by doing any one of the following, for these examples, we have a Subject with id `4321`::

    workflow.retire_subjects(4321)
    workflow.retire_subjects([4321])
    workflow.retire_subjects(Subject(4321))
    workflow.retire_subjects([Subject(4321)])

Similarly, we allow the ability to unretire subjects by subject by doing any one of the following, for these examples, we use a `Subject` with id `4321`::

    workflow.unretire_subjects(4321)
    workflow.unretire_subjects([4321])
    workflow.unretire_subjects(Subject(4321))
    workflow.unretire_subjects([Subject(4321)])

We also allow the ability to unretire subjects by `SubjectSet` by doing any on of the following, for these examples, we use a `SubjectSet` with id `5678`::

    workflow.unretire_subjects_by_subject_set(5678)
    workflow.unretire_subjects_by_subject_set([5678])
    workflow.unretire_subjects_by_subject_set(SubjectSet(5678))
    workflow.unretire_subjects_by_subject_set([SubjectSet(5678)])

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

Add subject set to first workflow in project::

    workflow = project.links.workflows[0]
    workflow.links.subject_sets.add(subject_set)

Look up user resource according to login / username::

    user_results = User.where(login='username')
    user = next(user_results)

Look up user resource for current logged in user::

    user = User.me()
    
Project owners and collaborators can update their users' project settings
(workflow_id only; for use with leveling up feature)::

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

Project owner/collaborator can also fetch all project settings for a project::

    project = Project.find("1234")

    pp_all = ProjectPreferences.fetch_settings(project=project)

    for pp in pp_all:
        print('Workflow ID: {}, User ID: {}'.format(pp.settings['workflow_id'], pp.raw['links']['user']))

Or the project settings for a particular user::

    project = Project.find("1234")
    user = User.find("1234")

    pp_all = ProjectPreferences.fetch_settings(project=project, user=user)

    pp = next(pp_all)
    print('Workflow ID: {}, User ID: {}'.format(pp.settings['workflow_id'], pp.raw['links']['user']))

Project settings can also be fetched with the project ID and user ID
directly if already known::

    pp_all = ProjectPreferences.fetch_settings(project=project_id, user=user_id)

    pp = next(pp_all)
    print('Workflow ID: {}, User ID: {}'.format(pp.settings['workflow_id'], pp.raw['links']['user']))

iNaturalist Imports
~~~~~~~~~~~~~~~~~~~
Importing iNaturalist observations to Panoptes as subjects is possible via an
API endpoint. Project owners and collaborators can use this client to send
a request to begin that import process::

    # The ID of the iNat taxon to be imported
    taxon_id = 1234

    # The subject set to which new subjects will be added
    subject_set_id = 5678

    Inaturalist.inat_import(taxon_id, subject_set_id)

As an optional parameter, the updated_since timestamp string can be included
and will filter obeservations by that parameter::

    Inaturalist.inat_import(taxon_id, subject_set_id, '2022-10-31')

Be aware that this command only initiates a background job on the Zooniverse
to import Observations. The request will return a 200 upon success, but there
is no progress to observe. You can refresh the subject set in the project builder
to see how far along it is, and the authenticated user will receive an email
when this job is completed.

Caesar features by Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Most Caesar use cases are usually through a workflow: the following are examples of Caesar functions that can be done via Workflow.

Add Caesar Extractor by Workflow::

    workflow = Workflow(1234)
    workflow.add_extractor('question', 'complete', 'T1', {'if_missing' : 'ignore'})

Add Reducer by Workflow::

    external_reducer_attributes = {
        'url': 'https://aggregation-caesar.zooniverse.org/reducers/optics_line_text_reducer',
        'filters': {
            'extractor_keys': ['alice']
        }
    }
    workflow.add_caesar_reducer('external', 'alice', external_reducer_attributes)

Adding Subject Rules by Workflow. When creating a rule, the `condition_string` argumentis a stringified array with the first item being a string identifying the operator. See https://zooniverse.github.io/caesar/#rules for examples of condition strings::

    condition_string = '["gte", ["lookup", "complete.0", 0], ["const", 30]]'
    workflow.add_caesar_rule(condition_string, 'subject')

Adding Subject Effect for a Subject Rule with id `1234` by Workflow. Ths particular effect being created will retire subjects early due to a consensus. ::

    workflow.add_caesar_rule_effect('subject', 1234, 'retire_subject', {'reason' : 'consensus'})

Project Copier
~~~~~~~~~~~~~~
The project copier feature clones an existing template project (i.e., projects which have the project.configuration `template` flag set as true and are not live).

You can set the template flag using the Project.save() method. See example below::

    project = Project(project_id)
    project.configuration = {"template": True}
    project.save()

**How to use**

This functionality can be accessed by the Panoptes python client. It exists on the Project module and can be called with the `copy` method::

    Project(project_id).copy()

You can also pass an optional `new_subject_set_name` parameter and this would be used to create a new SubjectSet for the newly cloned project::

    Project(project_id).copy(new_subject_set_name='My New Subject Set')

Data Exports
~~~~~~~~~~~~
The Panoptes Python Client allows you to generate, describe, and download data exports (e.g., classifications, subjects, workflows) via the Python ``panoptes_client`` library.

Multiple types of exports can be generated using the Python Client, including project-level products (classifications, subjects, workflows) and smaller scale classification exports (for workflows and subject sets).
For the examples below, we will demonstrate commands for a project wide classifications export, but these functions work for any export type.

**Get Exports**

As the name implies, this method downloads a data export over HTTP. This uses the `get_export` method and can be called by passing in the following parameters:

* *export_type*: string specifying which type of export should be downloaded.
* *generate*: a boolean specifying whether to generate a new export and wait for it to be ready, or to just download the latest existing export. Default is False.
* *wait*: a boolean specifying whether to wait for an in-progress export to finish, if there is one. Has no effect if `generate` is true (wait will occur in this case). Default is False.
* *wait_timeout*: the number of seconds to wait if `wait` is True or `generate` is True. Has no effect if `wait` and `generate` are both False. Default is None (wait indefinetly).

Examples::

    # Fetch existing export
    classification_export = Project(1234).get_export('classifications')

    # Generate export, wait indefinetly for result to complete
    classification_export = Project(1234).get_export('classifications', generate=True)

    # Fetch export currently being processed, wait up to 600 seconds for export to complete
    classification_export = Project(1234).get_export('classifications', wait=True, wait_timeout=600)

The returned Response object has two additional attributes as a convenience for working with the CSV content; `csv_reader` and `csv_dictreader`, which are wrappers for `csv.reader()` and `csv.DictReader` respectively.
These wrappers take care of correctly decoding the export content for the CSV parser::

    classification_export = Project(1234).get_export('classifications')
    for row in classification_export.csv_dictreader():
        print(row)

**Generate Exports**

As the name implies, this method generates/starts a data export. This uses the `generate_export` method and can be called by passing in the `export_type` parameter::

    export_info = Project(1234).generate_export('classifications')

This kick off the export generation process and returns `export_info` as a dictionary containing the metadata on the selected export.

**Describing Exports**

This method fetches information/metadata about a specific type of export. This uses the `describe_export` method and can be called by passing the `export_type` (e.g., classifications, subjects) this way::

    export_info = Project(1234).describe_export('classifications')

This would return `export_info` as a dictionary containing the metadata on the selected export.

Subject Set Classification Exports
++++++++++++++++++++++++++++++++++

As mentioned above, it is possible to request a classifications export for project, workflow, or subject set scope.
For the subject set classification export, classifications are included in the export if they satisfy two selection criteria:

1. The subject referenced in the classification is a member of the relevant subject set.
2. The relevant subject set is currently linked to the workflow referenced in the classification.

Example Usage::

    # For a SubjectSet, check which Workflows to which it is currently linked
    subject_set = SubjectSet.find(1234)
    for wf in subject_set.links.workflows:
        print(wf.id, wf.display_name)

    # Generate Export
    subject_set_classification_export = subject_set.get_export('classifications', generate=True)

Automated Aggregation of Classifications
++++++++++++++++++++++++++++++++++++++++

The Zooniverse supports research teams by maintaining the ``panoptes_aggregation`` Python package
(see `docs <https://aggregation-caesar.zooniverse.org/docs>`_ and `repo <https://github.com/zooniverse/aggregation-for-caesar>`_).
This software requires local installation to run, which can be a deterrent for its use.
As an alternative to installing and running this aggregation code, we provide a Zooniverse-hosted service for producing aggregated results for simple datasets.
This "batch aggregation" feature is built to perform simple workflow-level data aggregation that uses baseline extractors and reducers without any custom configuration.
Please see :py:meth:`.Workflow.run_aggregation` and :py:meth:`.Workflow.get_batch_aggregation_links` docstrings for full details.

Example Usage::

    # Generate input data exports: workflow-level classification export and project-level workflows export
    Workflow(1234).generate_export('classification')
    Project(2345).generate_export('workflows')

    # Request batch aggregation data product
    Workflow(1234).run_aggregation()

    # Fetch batch aggregation download URLs
    urls = Workflow(1234).get_batch_aggregation_links()
    print(urls)

    # Load Reductions CSV using Pandas
    pd.read_csv(urls['reductions'])
