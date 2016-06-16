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

    def __init__(self, raw={}, etag=None):
        r = super(SubjectSet, self).__init__(raw, etag)

        if self.id:
            self._edit_attributes[1]['links'] = (
                'subjects',
                'workflows',
            )

        return r

    def subjects(self):
        return Subject.where(subject_set_id=self.id)

    def add_subjects(self, subjects):
        if not type(subjects) in (tuple, list):
            subjects = [subjects]

        _subjects = []
        for subject in subjects:
            if not isinstance(subject, Subject):
                raise TypeError
            _subjects.append(subject.id)

        self.post(
            '{}/links/subjects'.format(self.id),
            json={'subjects': _subjects}
        )

LinkResolver.register(SubjectSet)
