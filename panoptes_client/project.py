import datetime
import requests
import time

from panoptes_client.panoptes import (
    LinkResolver, PanoptesAPIException, PanoptesObject
)

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
    )

    @classmethod
    def find(cls, id='', slug=None):
        if not id and not slug:
            return None
        return cls.where(id=id, slug=slug).next()

    def get_classifications_export(
        self,
        generate=False,
        wait=False,
        wait_timeout=60
    ):
        if generate:
            self.generate_classifications_export()

        if generate or wait:
            export = self.wait_classifications_export(wait_timeout)
        else:
            export = self.describe_classifications_export()

        return requests.get(
            export['media'][0]['src'],
            stream=True
        )

    def wait_classifications_export(self, timeout=60):
        success = False
        end_time = datetime.datetime.now() + datetime.timedelta(
            seconds=timeout
        )

        while datetime.datetime.now() < end_time:
            export_description = self.describe_classifications_export()
            export_metadata = export_description['media'][0]['metadata']
            if export_metadata.get('state', '') == 'ready':
                success = True
                break
            time.sleep(2)

        if not success:
            raise PanoptesAPIException(
                'classifications_export not ready within {} seconds'.format(
                    timeout
                )
            )

        return export_description

    def generate_classifications_export(self):
        return Project.post(
            self._classifications_export_path(),
            json = {"media":{"content_type":"text/csv"}}
        )[0]

    def describe_classifications_export(self):
        return Project.get(self._classifications_export_path())[0]

    def _classifications_export_path(self):
        return '{}/classifications_export'.format(self.id)

LinkResolver.register(Project)
