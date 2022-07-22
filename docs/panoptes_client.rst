panoptes\_client package
========================

As a convenience, the following classes can be imported directly from the root
of the ``panoptes_client`` package:

- :py:class:`.Panoptes`
- :py:class:`.Classification`
- :py:class:`.Collection`
- :py:class:`.Project`
- :py:class:`.ProjectPreferences`
- :py:class:`.Subject`
- :py:class:`.SubjectSet`
- :py:class:`.User`
- :py:class:`.Workflow`
- :py:class:`.Caesar`

For example::

    from panoptes_client import Panoptes, Project

    Panoptes.connect(username='example', password='example')

    new_project = Project()
    new_project.display_name = 'My new project'
    new_project.description = 'A great new project!'
    new_project.primary_language = 'en'
    new_project.private = True
    new_project.save()

panoptes\_client\.panoptes module
---------------------------------

.. automodule:: panoptes_client.panoptes
    :members:
    :show-inheritance:

panoptes\_client\.classification module
---------------------------------------

.. automodule:: panoptes_client.classification
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.collection module
-----------------------------------

.. automodule:: panoptes_client.collection
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.exportable module
-----------------------------------

.. automodule:: panoptes_client.exportable
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.project module
--------------------------------

.. automodule:: panoptes_client.project
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.project\_preferences module
---------------------------------------------

.. automodule:: panoptes_client.project_preferences
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.subject module
--------------------------------

.. automodule:: panoptes_client.subject
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.subject\_set module
-------------------------------------

.. automodule:: panoptes_client.subject_set
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.user module
-----------------------------

.. automodule:: panoptes_client.user
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.workflow module
---------------------------------

.. automodule:: panoptes_client.workflow
    :members:
    :undoc-members:
    :show-inheritance:

panoptes\_client\.workflow\_version module
------------------------------------------

.. automodule:: panoptes_client.workflow_version
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: http_get

panoptes\_client\.caesar module
------------------------------------------

.. automodule:: panoptes_client.caesar
    :members:
    :show-inheritance:
