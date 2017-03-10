from panoptes_client.panoptes import PanoptesObject
from panoptes_client.subject import Subject
from panoptes_client.utils import batchable


class Collection(PanoptesObject):
    _api_slug = 'collections'
    _link_slug = 'collections'
    _edit_attributes = (
        'name',
        'display_name',
        'private'
    )

    def subjects(self):
        return Subject.where(collection_id=self.id)

    # Add or remove subject links.
    # Takes a tuple or list of Subject objects
    # or a tuple or list of subject ids.
    @batchable
    def add(self, subjects):
        _subjects = self._build_subject_list(subjects)

        self.http_post(
            '{}/links/subjects'.format(self.id),
            json={'subjects': _subjects}
        )

    @batchable
    def remove(self, subjects):
        _subjects = self._build_subject_list(subjects)

        _subjects_ids = ",".join(_subjects)
        self.http_delete(
            '{}/links/subjects/{}'.format(self.id, _subjects_ids)
        )

    def _build_subject_list(self, subjects):
        _subjects = []
        for subject in subjects:
            if not (
                isinstance(subject, Subject)
                or isinstance(subject, (int, str, unicode,))
            ):
                raise TypeError

            if isinstance(subject, Subject):
                _subject_id = subject.id
            else:
                _subject_id = str(subject)

            _subjects.append(_subject_id)

        return _subjects
