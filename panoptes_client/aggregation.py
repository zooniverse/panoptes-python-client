from panoptes_client.panoptes import PanoptesObject


class Aggregation(PanoptesObject):
    _api_slug = 'aggregations'
    _link_slug = 'aggregations'
    _edit_attributes = (
        {
            'links': (
                'workflow',
                'user',
            )
        },
    )
