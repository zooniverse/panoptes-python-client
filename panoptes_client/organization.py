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

    def add(self, projects):
        """
        A wrapper around :py:meth:`.LinkCollection.add`. Equivalent to::

            organization.links.add(projects)
        """

        return self.links.projects.add(projects)

    def remove(self, projects):
        """
        A wrapper around :py:meth:`.LinkCollection.remove`. Equivalent to::

            organization.links.remove(projects)
        """

        return self.links.projects.remove(projects)

    def __contains__(self, project):
        """
        A wrapper around :py:meth:`.LinkCollection.__contains__`. Equivalent
        to::

            project in organization.links.project
        """

        return project in self


LinkResolver.register(Organization)
