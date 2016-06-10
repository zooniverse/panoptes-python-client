from panoptes_client.panoptes import PanoptesObject, LinkResolver

class Project(PanoptesObject):
    _api_slug = 'projects'
    _link_slug = 'project'
    _edit_attributes = (
        'display_name',
        'description',
        'tags',
        'introduction',
        'private',
        'primary_language',
        {
            'links': (
                'workflows',
                'subject_sets',
            )
        },
    )

    @classmethod
    def find(cls, _id='', slug=None, display_name=None):
        params = {
            'slug': slug,
            'display_name': display_name,
        }

        return super(Project, cls).find(_id, params)

LinkResolver.register(Project)
