from panoptes_client.panoptes import PanoptesObject, LinkResolver


class SetMemberSubject(PanoptesObject):
    _api_slug = 'set_member_subjects'
    _link_slug = 'set_member_subjects'
    _edit_attributes = (
        'priority',
    )

LinkResolver.register(SetMemberSubject)
LinkResolver.register(SetMemberSubject, 'set_member_subject')
