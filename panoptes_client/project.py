import datetime
import requests
import time

from panoptes_client.panoptes import (
    LinkResolver, PanoptesAPIException, PanoptesObject
)

TALK_EXPORT_TYPES = (
    'talk_comments',
    'talk_tags',
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

    def get_export(
        self,
        export_type,
        generate=False,
        wait=False,
        wait_timeout=60
    ):
        if export_type in TALK_EXPORT_TYPES:
            return self._get_talk_export(
                export_type,
                generate,
                wait,
                wait_timeout
            )

        if generate:
            self.generate_export(export_type)

        if generate or wait:
            export = self.wait_export(export_type, wait_timeout)
        else:
            export = self.describe_export(export_type)

        return requests.get(
            export['media'][0]['src'],
            stream=True
        )

    def wait_export(self, export_type, timeout=60):
        if export_type in TALK_EXPORT_TYPES:
            return self._wait_talk_export(export_type, timeout)

        success = False
        end_time = datetime.datetime.now() + datetime.timedelta(
            seconds=timeout
        )

        while datetime.datetime.now() < end_time:
            export_description = self.describe_export(export_type)
            if export_description:
                export_metadata = export_description['media'][0]['metadata']
                if export_metadata.get('state', '') == 'ready':
                    success = True
                    break
            time.sleep(2)

        if not success:
            raise PanoptesAPIException(
                '{}_export not ready within {} seconds'.format(
                    export_type,
                    timeout
                )
            )

        return export_description

    def generate_export(self, export_type):
        if export_type in TALK_EXPORT_TYPES:
            return self._generate_talk_export(export_type)

        return Project.post(
            self._export_path(export_type),
            json = {"media":{"content_type":"text/csv"}}
        )[0]

    def describe_export(self, export_type):
        if export_type in TALK_EXPORT_TYPES:
            return self._describe_talk_export(export_type)

        return Project.get(self._export_path(export_type))[0]

    def _get_talk_export(
        self,
        export_type,
        generate,
        wait,
        wait_timeout
    ):
        raise NotImplementedError('Talk exports are not yet supported')

    def _wait_talk_export(self, export_type, timeout):
        raise NotImplementedError('Talk exports are not yet supported')

    def _generate_talk_export(self, export_type):
        raise NotImplementedError('Talk exports are not yet supported')

    def _describe_talk_export(self, export_type):
        raise NotImplementedError('Talk exports are not yet supported')

    def _export_path(self, export_type):
        return '{}/{}_export'.format(export_type, self.id)

LinkResolver.register(Project)
