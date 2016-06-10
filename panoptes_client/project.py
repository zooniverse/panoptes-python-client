from panoptes_client.panoptes import PanoptesObject

class Project(PanoptesObject):
    _api_slug = 'projects'

    @classmethod
    def find(cls, project_id='', slug=None, display_name=None):
        if project_id is None:
            project_id = ''

        params = {
            'slug': slug,
            'display_name': display_name,
        }

        return cls.paginated_results(cls.get(project_id, params=params))

    def __repr__(self):
        return '<Project {}>'.format(self.id)
