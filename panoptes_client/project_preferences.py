from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.project import Project
from panoptes_client.user import User

class ProjectPreferences(PanoptesObject):
    """
    Contains the settings for a :py:class:`.User` on a :py:class:`.Project`.
    """

    _api_slug = 'project_preferences'
    _link_slug = 'project_preferences'
    _edit_attributes = (
        'preferences',
        'settings',
    )

    @classmethod
    def find(cls, id='', user=None, project=None):
        """
        Like :py:meth:`.PanoptesObject.find` but can also query by user and
        project.

        - **user** and **project** can be either a :py:class:`.User` and
          :py:class:`.Project` instance respectively, or they can be given as
          IDs. If either argument is given, the other is also required.
        """

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
                isinstance(user, (int, str,))
                and isinstance(project, (int, str,))
            ):
                _user_id = user
                _project_id = project
            else:
                raise TypeError
            id = cls.where(user_id=_user_id, project_id=_project_id).next().id
        return super(ProjectPreferences, cls).find(id)

    @classmethod
    def save_settings(cls, project=None, user=None, settings=None):
        """
        Save settings for a user without first fetching their preferences.

        - **user** and **project** can be either a :py:class:`.User` and
          :py:class:`.Project` instance respectively, or they can be given as
          IDs. If either argument is given, the other is also required.
        - **settings** is a :py:class:`dict` containing the settings to be
          saved.
        """

        if (isinstance(settings, dict)):
            _to_update = settings
            if (
                isinstance(user, User)
                and isinstance(project, Project)
            ):
                _user_id = user.id
                _project_id = project.id
            elif (
                isinstance(user, (int, str,))
                and isinstance(project, (int, str,))
            ):
                _user_id = user
                _project_id = project
            else:
                raise TypeError
            cls.http_post(
                'update_settings',
                json={
                    'project_preferences': {
                        'user_id': _user_id,
                        'project_id': _project_id,
                        'settings': _to_update,
                    }
                }
            )
        else:
            raise TypeError

LinkResolver.register(ProjectPreferences)
