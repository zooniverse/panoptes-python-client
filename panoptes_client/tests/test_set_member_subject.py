import unittest

from panoptes_client import SetMemberSubject


class TestSetMemberSubject(unittest.TestCase):
    def test_find_id(self):
        sms = SetMemberSubject.find(1000)
        self.assertEqual(sms.id, '1000')

    def test_subject_set_id(self):
        sms = SetMemberSubject.find(1000)
        self.assertEqual(sms.subject_set_id(), '2')

    def test_subject_id(self):
        sms = SetMemberSubject.find(1000)
        self.assertEqual(sms.subject_id(), '1458')
