from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.project import Project
from panoptes_client.user import User

class ProjectPreferences(PanoptesObject):
    _api_slug = 'project_preferences'
    _link_slug = 'project_preferences'
    _edit_attributes = (
        'preferences',
    )

    @classmethod
    def find(cls, id='', user=None, project=None):
        if not id:
            if not (user and project):
                raise ValueError('Both user and project required')
            if (
                isinstance(user, User)
                and isinstance(project, Project)
            ):
                _user_id = user.id
                _project_id = project.id
            elif (
                isinstance(user, (int, str, unicode,))
                and isinstance(project, (int, str, unicode,))
            ):
                _user_id = user
                _project_id = project
            else:
                raise TypeError
            id = cls.where(user_id=_user_id, project_id=_project_id).next().id
        return super(ProjectPreferences, cls).find(id)

LinkResolver.register(ProjectPreferences)
