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
        if not id and not slug:
            return None
        try:
            return cls.where(id=id, slug=slug).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find project with slug='{}'".format(slug)
            )

    def collaborators(self, *roles):
        return [
            r.links.owner for r in ProjectRole.where(project_id=self.id)
            if len(roles) == 0 or len(set(roles) & set(r.roles)) > 0
        ]

    @batchable
    def add_links(self, linked_objects, link_type):
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
        return self.add_links(
            subject_sets,
            'subject_sets',
        )

    def add_workflows(self, workflows):
        return self.add_links(
            workflows,
            'workflows',
        )

LinkResolver.register(Project)
