from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import PanoptesObject, LinkResolver


class CollectionRole(PanoptesObject):
    _api_slug = 'collection_roles'
    _link_slug = 'collection_roles'
    _edit_attributes = (
        'roles',
        {
            'links': (
                'collection',
                'user',
            ),
        },
    )


LinkResolver.register(CollectionRole)
