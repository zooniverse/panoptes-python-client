from panoptes_client.panoptes import PanoptesObject, LinkResolver


class ProjectPreferences(PanoptesObject):
    _api_slug = 'project_preferences'
    _link_slug = 'project_preferences'
    _edit_attributes = (
        'preferences',
    )

    @classmethod
    def find(cls, id='', user_id=None, project_id=None):
        if not id:
            if not (user_id and project_id):
                raise ValueError('Both user_id and project_id required')
            id = cls.where(user_id=user_id, project_id=project_id).next().id
        return super(ProjectPreferences, cls).find(id)

LinkResolver.register(ProjectPreferences)
