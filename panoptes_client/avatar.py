from panoptes_client.panoptes import (
    Panoptes,
    PanoptesAPIException,
    PanoptesObject,
    LinkResolver,
)
from panoptes_client.project import Project


class Avatar(PanoptesObject):
    _api_slug = 'avatar'
    _link_slug = 'avatars'
    _edit_attributes = ()

    @classmethod
    def http_get(cls, path, params={}, headers={}):
        project = params.pop('project')
        # print()
        # print(Project.url(project.id))
        # print()

        avatar_response = Panoptes.client().get(
            Project.url(project.id) + cls.url(path),
            params,
            headers,
        )
        print(avatar_response.raw)
        return avatar_response


LinkResolver.register(Avatar)
LinkResolver.register(Avatar, 'avatar')
