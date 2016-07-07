from panoptes_client.panoptes import PanoptesObject, LinkResolver
from panoptes_client.subject import Subject

class Workflow(PanoptesObject):
    _api_slug = 'workflows'
    _link_slug = 'workflows'
    _edit_attributes = []

    def retire_subjects(self, subjects, reason='other'):
        if type(subjects) not in (list, tuple):
            subjects = [ subjects ]
        subjects = [ s.id if isinstance(s, Subject) else s for s in subjects ]

        return Workflow.post(
            '{}/retired_subjects'.format(self.id),
            json={
                'subject_ids': subjects,
                'retirement_reason': reason
            }
        )

LinkResolver.register(Workflow)
