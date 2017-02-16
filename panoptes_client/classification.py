from panoptes_client.panoptes import LinkResolver, PanoptesObject


class Classification(PanoptesObject):
    _api_slug = 'classifications'
    _link_slug = 'classification'
    _edit_attributes = ( )

    @classmethod
    def where(cls, **kwargs):
        scope = kwargs.pop('scope', None)
        if not scope:
            return super(Classification, cls).where(**kwargs)
        return cls.paginated_results(*cls.http_get(scope, params=kwargs))

LinkResolver.register(Classification)
