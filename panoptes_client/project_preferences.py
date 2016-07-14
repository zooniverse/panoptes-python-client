from panoptes_client.panoptes import PanoptesObject, LinkResolver

class ProjectPreferences(PanoptesObject):
    _api_slug = 'project_preferences'
    _link_slug = 'project_preferences'
    _edit_attributes = (
        'preferences',
    )

    @classmethod
    def find(cls, user_id, project_id):
        return cls.where(user_id=user_id, project_id=project_id).next()

LinkResolver.register(ProjectPreferences)