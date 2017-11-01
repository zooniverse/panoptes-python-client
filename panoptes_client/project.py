from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import (
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.project_role import ProjectRole
from panoptes_client.exportable import Exportable
from panoptes_client.utils import batchable


class Project(PanoptesObject, Exportable):
    _api_slug = 'projects'
    _link_slug = 'project'
    _edit_attributes = (
        'display_name',
        'description',
        'tags',
        'introduction',
        'private',
        'primary_language',
    )

    @classmethod
    def find(cls, id='', slug=None):
        """
        Similar to :py:meth:`.PanoptesObject.find`, but allows lookup by slug
        as well as ID.

        Examples::

            project_1234 = Project.find(1234)
            galaxy_zoo = Project.find(slug="zooniverse/galaxy-zoo")
        """

        if not id and not slug:
            return None
        try:
            return cls.where(id=id, slug=slug).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find project with slug='{}'".format(slug)
            )

    def collaborators(self, *roles):
        """
        Returns a list of :py:class:`.User` who are collaborators on this
        project.

        Zero or more role arguments can be passed as strings to narrow down the
        results. If any roles are given, users who possess at least one of the
        given roles are returned.

        Examples::

            all_collabs = project.collaborators()
            moderators = project.collaborators("moderators")
            moderators_and_translators = project.collaborators(
                "moderators",
                "translators",
            )
        """

        return [
            r.links.owner for r in ProjectRole.where(project_id=self.id)
            if len(roles) == 0 or len(set(roles) & set(r.roles)) > 0
        ]

    @batchable
    def _add_links(self, linked_objects, link_type):
        object_ids = []

        for linked_object in linked_objects:
            if hasattr(linked_object, 'id'):
                object_ids.append(linked_object.id)
            else:
                object_ids.append(str(linked_object))

        self.http_post(
            '{}/links/{}'.format(self.id, link_type),
            json={
                link_type: object_ids
            }
        )

    def add_subject_sets(self, subject_sets):
        """
        Links the given subject sets to this project. New subject sets are
        created as copies of the given sets.

        - **subject_sets** can be a list of :py:class:`.SubjectSet`
          instances, a list of subject set IDs, a single
          :py:class:`.SubjectSet` instance, or a single subject set ID.

        Examples::

            project.add_subject_sets(1234)
            project.add_subject_sets([1,2,3,4])
            project.add_subject_sets(SubjectSet(1234))
            project.add_subject_sets([SubjectSet(12), SubjectSet(34)])
        """

        return self._add_links(
            subject_sets,
            'subject_sets',
        )

    def add_workflows(self, workflows):
        """
        Links the given workflows to this project. New workflows are
        created as copies of the given workflows.

        - **workflows** can be a list of :py:class:`.Workflow` instances,
          a list of workflow IDs, a single :py:class:`.Workflow`
          instance, or a single workflow ID.

        Examples::

            project.add_workflows(1234)
            project.add_workflows([1,2,3,4])
            project.add_workflows(Workflow(1234))
            project.add_workflows([Workflow(12), Workflow(34)])
        """
        return self._add_links(
            workflows,
            'workflows',
        )

LinkResolver.register(Project)
LinkResolver.register(Project, 'projects')
