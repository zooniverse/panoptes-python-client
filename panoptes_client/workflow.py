from panoptes_client.exportable import Exportable
from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject
from panoptes_client.subject_set import SubjectSet
from panoptes_client.utils import batchable


class Workflow(PanoptesObject, Exportable):
    _api_slug = 'workflows'
    _link_slug = 'workflows'
    _edit_attributes = (
        'tasks',
        'first_task',
        'configuration',
        'display_name',
        'active',
    )

    @batchable
    def retire_subjects(self, subjects, reason='other'):
        subjects = [ s.id if isinstance(s, Subject) else s for s in subjects ]

        return Workflow.http_post(
            '{}/retired_subjects'.format(self.id),
            json={
                'subject_ids': subjects,
                'retirement_reason': reason
            }
        )

    @batchable
    def add_subject_sets(self, subject_sets):
        _subject_sets = self._build_subject_set_list(subject_sets)

        self.post(
            '{}/links/subject_sets'.format(self.id),
            json={'subject_sets': _subject_sets}
        )

    @batchable
    def remove_subject_sets(self, subject_sets):
        _subject_sets = self._build_subject_set_list(subject_sets)
        _subject_set_ids = ",".join(_subject_sets)

        self.http_delete(
            '{}/links/subject_sets/{}'.format(self.id, _subject_set_ids)
        )

    def _build_subject_set_list(self, subject_sets):
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
