from panoptes_client.panoptes import (
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.project_role import ProjectRole
from panoptes_client.exportable import Exportable


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


LinkResolver.register(Project)
