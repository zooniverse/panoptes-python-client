from panoptes_client.panoptes import PanoptesObject, LinkResolver


class ProjectRole(PanoptesObject):
    _api_slug = 'project_roles'
    _link_slug = 'project_roles'
    _edit_attributes = ()

LinkResolver.register(ProjectRole)
