from __future__ import absolute_import, division, print_function
from copy import deepcopy

from panoptes_client.panoptes import (
    LinkCollection,
    LinkResolver,
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.project_role import ProjectRole
from panoptes_client.exportable import Exportable
from panoptes_client.utils import batchable

class ProjectLinkCollection(LinkCollection):
    def add(self, objs):
        from panoptes_client.workflow import Workflow
        from panoptes_client.subject_set import SubjectSet

        result = super(ProjectLinkCollection, self).add(objs)

        # Some classes are copied into the project as new objects
        # So we reload to pick those up.
        if self._cls in (SubjectSet, Workflow):
            self._parent.reload()

        return result


class Project(PanoptesObject, Exportable):
    _api_slug = 'projects'
    _link_slug = 'project'
    _edit_attributes = (
        'display_name',
        'description',
        'tags',
        'introduction',
        'private',
        'primary_language',
        'configuration',
    )
    _link_collection = ProjectLinkCollection

    def __init__(self, raw={}, etag=None):
        super(Project, self).__init__(raw, etag)
        if not self.configuration:
            self.configuration = {}
            self._original_configuration = {}

    def set_raw(self, raw, etag=None, loaded=True):
        super(Project, self).set_raw(raw, etag, loaded)
        if loaded and self.configuration:
            self._original_configuration = deepcopy(self.configuration)
        elif loaded:
            self._original_configuration = None

    def save(self):
        """
        Adds project configuration to the list of savable attributes
        if it has changed.
        """
        if not self.configuration == self._original_configuration:
            self.modified_attributes.add('configuration')

        super(Project, self).save()

    @classmethod
    def find(cls, id='', slug=None):
        """
        Similar to :py:meth:`.PanoptesObject.find`, but allows lookup by slug
        as well as ID.

        Examples::

            project_1234 = Project.find(1234)
            galaxy_zoo = Project.find(slug="zooniverse/galaxy-zoo")
        """

        if not id and not slug:
            return None
        try:
            return cls.where(id=id, slug=slug).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find project with slug='{}'".format(slug)
            )

    def collaborators(self, *roles):
        """
        Returns a list of :py:class:`.User` who are collaborators on this
        project.

        Zero or more role arguments can be passed as strings to narrow down the
        results. If any roles are given, users who possess at least one of the
        given roles are returned.

        Examples::

            all_collabs = project.collaborators()
            moderators = project.collaborators("moderators")
            moderators_and_translators = project.collaborators(
                "moderators",
                "translators",
            )
        """

        return [
            r.links.owner for r in ProjectRole.where(project_id=self.id)
            if len(roles) == 0 or len(set(roles) & set(r.roles)) > 0
        ]

    @batchable
    def _add_links(self, linked_objects, link_type):
        object_ids = []

        for linked_object in linked_objects:
            if hasattr(linked_object, 'id'):
                object_ids.append(linked_object.id)
            else:
                object_ids.append(str(linked_object))

        self.http_post(
            '{}/links/{}'.format(self.id, link_type),
            json={
                link_type: object_ids
            }
        )

    def add_subject_sets(self, subject_sets):
        """
        Links the given subject sets to this project. New subject sets are
        created as copies of the given sets.

        - **subject_sets** can be a list of :py:class:`.SubjectSet`
          instances, a list of subject set IDs, a single
          :py:class:`.SubjectSet` instance, or a single subject set ID.

        Examples::

            project.add_subject_sets(1234)
            project.add_subject_sets([1,2,3,4])
            project.add_subject_sets(SubjectSet(1234))
            project.add_subject_sets([SubjectSet(12), SubjectSet(34)])
        """

        return self._add_links(
            subject_sets,
            'subject_sets',
        )

    def add_workflows(self, workflows):
        """
        Links the given workflows to this project. New workflows are
        created as copies of the given workflows.

        - **workflows** can be a list of :py:class:`.Workflow` instances,
          a list of workflow IDs, a single :py:class:`.Workflow`
          instance, or a single workflow ID.

        Examples::

            project.add_workflows(1234)
            project.add_workflows([1,2,3,4])
            project.add_workflows(Workflow(1234))
            project.add_workflows([Workflow(12), Workflow(34)])
        """
        return self._add_links(
            workflows,
            'workflows',
        )

    @property
    def avatar(self):
        """
        A dict containing metadata about the project's avatar.
        """
        return self.http_get('{}/avatar'.format(self.id))[0]

    @property
    def attached_images(self):
        return self.http_get('{}/attached_images'.format(self.id))[0]

    def add_attached_image(
        self,
        src,
        content_type='image/png',
        external_link=True,
        metadata={},
    ):
        return self.http_post(
            '{}/attached_images'.format(self.id),
            json={'media': {
                'src': src,
                'content_type': content_type,
                'external_link': external_link,
                'metadata': metadata,
            }},
        )

    def copy(self, new_subject_set_name=None):
        """
        Copy this project to a new project that will be owned by the
        currently authenticated user.

        A new_subject_set_name string argument can be passed which will be
        used to name a new SubjectSet for the copied project.
        This is useful for having an upload target straight after cloning.

        Examples::

            project.copy()
            project.copy("My new subject set for uploading")
        """
        payload = {}
        if new_subject_set_name:
            payload['create_subject_set'] = new_subject_set_name

        response = self.http_post(
            '{}/copy'.format(self.id),
            json=payload,
        )

        # find the API resource response in the response tuple
        resource_response = response[0]
        # save the etag from the copied project response
        etag = response[1]
        # extract the raw copied project resource response
        raw_resource_response = resource_response[self._api_slug][0]

        # convert it into a new project model representation
        # ensure we provide the etag - without it the resource won't be savable
        copied_project = Project(raw_resource_response, etag)

        return copied_project


LinkResolver.register(Project)
LinkResolver.register(Project, 'projects')
