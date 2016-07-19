from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject

class SubjectSet(PanoptesObject):
    _api_slug = 'subject_sets'
    _link_slug = 'subject_sets'
    _edit_attributes = (
        'display_name',
        {
            'links': (
                'project',
            ),
            'metadata': (
                'category',
            )
        },
    )

    def subjects(self):
        return Subject.where(subject_set_id=self.id)

    # Add or remove subject links.
    # Takes a tuple or list of Subject objects
    # or a tuple or list of subject ids.
    def add(self, subjects):
        _subjects = self._build_subject_list(subjects)

        self.post(
            '{}/links/subjects'.format(self.id),
            json={'subjects': _subjects}
        )

    def remove(self, subjects):
        _subjects = self._build_subject_list(subjects)
        _subjects_ids = ",".join(_subjects)

        self.delete(
            '{}/links/subjects/{}'.format(self.id, _subjects_ids)
        )

    def _build_subject_list(self, subjects):
        if not type(subjects) in (tuple, list):
            subjects = [subjects]

        _subjects = []
        for subject in subjects:
            if not (
                isinstance(subject, Subject)
                or isinstance(subject, (int, str,
            unicode,))
            ):
                raise TypeError

            if isinstance(subject, Subject):
                _subject_id = subject.id
            else:
                _subject_id = str(subject)

            _subjects.append(_subject_id)

        return _subjects

LinkResolver.register(SubjectSet)
