from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import LinkResolver, PanoptesObject


class Classification(PanoptesObject):
    _api_slug = 'classifications'
    _link_slug = 'classification'
    _edit_attributes = ( )

    @classmethod
    def where(cls, **kwargs):
        """
        where(scope=None, **kwargs)

        Like :py:meth:`.PanoptesObject.where`, but also allows setting the
        query scope.

        - **scope** can be any of the values given in the `Classification
          Collection API documentation <http://docs.panoptes.apiary.io/#reference/classification/classification/list-all-classifications>`_
          without the leading slash.

        Examples::

            my_classifications = Classification.where()
            my_proj_123_classifications = Classification.where(project_id=123)

            all_proj_123_classifications = Classification.where(
                scope='project',
                project_id=123,
            )
        """

        scope = kwargs.pop('scope', None)
        if not scope:
            return super(Classification, cls).where(**kwargs)
        return cls.paginated_results(*cls.http_get(scope, params=kwargs))

LinkResolver.register(Classification)
