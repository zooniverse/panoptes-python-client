import unittest

from panoptes_client.set_member_subject import SetMemberSubject


class TestSetMemberSubject(unittest.TestCase):
    def test_find_id(self):
        sms = SetMemberSubject.find(1000)
        self.assertEqual(sms.id, '1000')
