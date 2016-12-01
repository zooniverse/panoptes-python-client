from panoptes_client.panoptes import PanoptesObject, LinkResolver

class SetMemberSubject(PanoptesObject):
    _api_slug = 'set_member_subjects'
    _link_slug = 'set_member_subjects'
    _edit_attributes = ()

    def subject_set_id(self):
        return self.raw['links']['subject_set']

    def subject_id(self):
        return self.raw['links']['subject']

LinkResolver.register(SetMemberSubject)
LinkResolver.register(SetMemberSubject, 'set_member_subject')
