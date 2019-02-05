from __future__ import absolute_import, division, print_function
from builtins import str

from panoptes_client.panoptes import (
    PanoptesAPIException,
    PanoptesObject,
)
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable


class Collection(PanoptesObject):
    _api_slug = 'collections'
    _link_slug = 'collections'
    _edit_attributes = (
        'name',
        'description',
        'display_name',
        'private',
        {
            'links': (
                'project',
            ),
        },
    )

    @classmethod
    def find(cls, id='', slug=None):
        """
        Similar to :py:meth:`.PanoptesObject.find`, but allows lookup by slug
        as well as ID.

        Examples::

            collection_1234 = Collection.find(1234)
            my_collection = Collection.find(slug="example/my-collection")
        """

        if not id and not slug:
            return None
        try:
            return cls.where(id=id, slug=slug).next()
        except StopIteration:
            raise PanoptesAPIException(
                "Could not find collection with slug='{}'".format(slug)
            )

    @property
    def subjects(self):
        """
        A generator which yields each :py:class:`.Subject` in this collection.
        """

        return self.links.subjects

    def add(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.add`. Equivalent to::

            collection.links.add(subjects)
        """

        return self.links.subjects.add(subjects)

    def remove(self, subjects):
        """
        A wrapper around :py:meth:`.LinkCollection.remove`. Equivalent to::

            collection.links.remove(subjects)
        """

        return self.links.subjects.remove(subjects)

    def set_default_subject(self, subject):
        """
        Sets the subject's location media URL as a link.
        It displays as the default subject on PFE.

        - **subject** can be a single :py:class:`.Subject` instance or a single
          subject ID.

        Examples::

            collection.set_default_subject(1234)
            collection.set_default_subject(Subject(1234))
        """
        if not (
            isinstance(subject, Subject)
            or isinstance(subject, (int, str,))
        ):
            raise TypeError
        if isinstance(subject, Subject):
            _subject_id = subject.id
        else:
            _subject_id = str(subject)

        self.http_post(
            '{}/links/default_subject'.format(self.id),
            json={'default_subject': _subject_id},
        )
