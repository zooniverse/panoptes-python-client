from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject
from panoptes_client.subject_set import SubjectSet


class Workflow(PanoptesObject):
    _api_slug = 'workflows'
    _link_slug = 'workflows'
    _edit_attributes = []

    def retire_subjects(self, subjects, reason='other'):
        if type(subjects) not in (list, tuple, set):
            subjects = [ subjects ]
        subjects = [ s.id if isinstance(s, Subject) else s for s in subjects ]

        return Workflow.post(
            '{}/retired_subjects'.format(self.id),
            json={
                'subject_ids': subjects,
                'retirement_reason': reason
            }
        )

    def add_subject_sets(self, subject_sets, batch_size=100):
        _subject_sets = self._build_subject_set_list(subject_sets)

        for _subject_sets_batch in [
            _subject_sets[i:i+batch_size]
            for i in xrange(0, len(_subject_sets), batch_size)
        ]:
            self.post(
                '{}/links/subject_sets'.format(self.id),
                json={'subject_sets': _subject_sets_batch}
            )

    def remove_subject_sets(self, subject_sets):
        _subject_sets = self._build_subject_set_list(subject_sets)
        _subject_set_ids = ",".join(_subject_sets)

        self.delete(
            '{}/links/subject_sets/{}'.format(self.id, _subject_set_ids)
        )

    def _build_subject_set_list(self, subject_sets):
        if not type(subject_sets) in (tuple, list, set):
            subject_sets = [subject_sets]

        _subject_sets = []
        for subject_set in subject_sets:
            if not (
                isinstance(subject_set, SubjectSet)
                or isinstance(subject_set, (int, str, unicode,))
            ):
                raise TypeError

            if isinstance(subject_set, SubjectSet):
                _subject_set_id = subject_set.id
            else:
                _subject_set_id = str(subject_set)

            _subject_sets.append(_subject_set_id)

        return _subject_sets

LinkResolver.register(Workflow)
