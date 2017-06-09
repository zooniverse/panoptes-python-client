from __future__ import absolute_import, division, print_function

from panoptes_client.panoptes import (
    Panoptes,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.workflow import Workflow


class WorkflowVersion(PanoptesObject):
    _api_slug = 'versions'
    _edit_attributes = tuple()

    @classmethod
    def http_get(cls, path, params={}, headers={}):
        workflow = params.pop('workflow')
        return Panoptes.client().get(
            Workflow.url(workflow.id) + cls.url(path),
            params,
            headers,
        )

    @classmethod
    def find(cls, _id, workflow):
        try:
            return cls.where(id=_id, workflow=workflow).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find {} with id='{}'".format(cls.__name__, _id)
            )

    def save(self):
        raise NotImplementedError(
            'It is not possible to manually create workflow versions. '
            'Modify the workflow instead.'
        )

    @property
    def workflow(self):
        return self.links.item
