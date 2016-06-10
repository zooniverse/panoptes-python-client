from panoptes_client.panoptes import PanoptesObject, LinkResolver

class Project(PanoptesObject):
    _api_slug = 'projects'
    _link_slug = 'project'

    @classmethod
    def find(cls, _id='', slug=None, display_name=None):
        params = {
            'slug': slug,
            'display_name': display_name,
        }

        return super(Project, cls).find(_id, params)

LinkResolver.register(Project)
