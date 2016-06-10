from panoptes_client.panoptes import PanoptesObject

class Project(PanoptesObject):
    slug = 'projects'

    @classmethod
    def find(cls, project_id='', slug=None, display_name=None):
        if project_id is None:
            project_id = ''

        params = {
            'slug': slug,
            'display_name': display_name,
        }

        return map(Project, cls.get(project_id, params=params)['projects'])

    def __repr__(self):
        return "Project ID %s: %s" % (self.id, self.title)
