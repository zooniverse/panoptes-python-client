from panoptes_client.panoptes import (
    Panoptes,
    PanoptesObject,
    LinkResolver,
)
from panoptes_client.project import Project


class ProjectAvatar(PanoptesObject):
    _api_slug = 'avatar'
    _link_slug = 'avatars'
    _edit_attributes = ()

    @classmethod
    def avatar_get(cls, path, params={}, headers={}):
        project = params.pop('project')

        avatar_response = Panoptes.client().get(
            Project.url(project.id) + cls.url(path),
            params,
            headers,
        )
        return avatar_response


LinkResolver.register(Avatar)
LinkResolver.register(Avatar, 'avatar')
