from panoptes_client.panoptes import PanoptesObject
from panoptes_client.subject import Subject


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
    def add(self, subjects, batch_size=100):
        _subjects = self._build_subject_list(subjects)

        for _subjects_batch in [
            _subjects[i:i+batch_size]
            for i in xrange(0, len(_subjects), batch_size)
        ]:
            self.post(
                '{}/links/subjects'.format(self.id),
                json={'subjects': _subjects_batch}
            )

    def remove(self, subjects, batch_size=100):
        _subjects = self._build_subject_list(subjects)

        for _subjects_batch in [
            _subjects[i:i+batch_size]
            for i in xrange(0, len(_subjects), batch_size)
        ]:
            _subjects_ids = ",".join(_subjects_batch)
            self.delete(
                '{}/links/subjects/{}'.format(self.id, _subjects_ids)
            )

    def _build_subject_list(self, subjects):
        if not type(subjects) in (tuple, list, set):
            subjects = [subjects]

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
