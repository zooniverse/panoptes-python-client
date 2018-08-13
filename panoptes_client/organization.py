from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import (
    LinkResolver,
    PanoptesObject,
)
from panoptes_client.project import Project
from panoptes_client.utils import batchable


class Organization(PanoptesObject):
    _api_slug = 'organizations'
    _link_slug = 'organization'
    _edit_attributes = (
        'display_name',
        'description',
        'tags',
        'introduction',
        'primary_language',
    )

    @batchable
    def add(self, projects):
        """
        Links the given projects to this organization.

        - **projects** can be a list of :py:class:`.Project` instances, a list
          of project IDs, a single :py:class:`.Project` instance, or a single
          project ID.

        Examples::

            organization.add(1234)
            organization.add([1,2,3,4])
            organization.add(Project(1234))
            organization.add([Project(12), Project(34)])
        """

        _projects = self._build_project_list(projects)

        self.http_post(
            '{}/links/projects'.format(self.id),
            json={'projects': _projects}
        )

    @batchable
    def remove(self, projects):
        """
        Unlinks the given projects from this organization.

        - **projects** can be a list of :py:class:`.Project` instances, a list
          of project IDs, a single :py:class:`.Project` instance, or a single
          project ID.

        Examples::

            organization.remove(1234)
            organization.remove([1,2,3,4])
            organization.remove(Project(1234))
            organization.remove([Project(12), Project(34)])
        """

        _projects = self._build_project_list(projects)

        _project_ids = ",".join(_projects)
        self.http_delete(
            '{}/links/projects/{}'.format(self.id, _project_ids)
        )

    def __contains__(self, project):
        """
        Tests if the project is linked to this organization.

        - **project** a single :py:class:`.Project` instance, or a single
          project ID.

        Returns a boolean indicating if the project is linked to the
        organization.

        Examples::
            1234 in organization
            Project(1234) in organization
        """
        if not self._loaded:
            self.reload()

        if isinstance(project, Project):
            project_id = str(project.id)
        else:
            project_id = str(project)

        return project_id in self.raw.get('links', {}).get('projects', [])

    def _build_project_list(self, projects):
        _projects = []
        for project in projects:
            if not (
                isinstance(project, Project)
                or isinstance(project, (int, str,))
            ):
                raise TypeError

            if isinstance(project, Project):
                _project_id = str(project.id)
            else:
                _project_id = str(project)

            _projects.append(_project_id)

        return _projects


LinkResolver.register(Organization)
