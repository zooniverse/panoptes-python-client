import unittest
import sys
from panoptes_client.panoptes import PanoptesAPIException
from panoptes_client.workflow import Workflow
from panoptes_client.caesar import Caesar

if sys.version_info <= (3, 0):
    from mock import patch
else:
    from unittest.mock import patch


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        super().setUp()
        caesar_post_patch = patch.object(Caesar, 'http_post')
        caesar_put_patch = patch.object(Caesar, 'http_put')
        caesar_get_patch = patch.object(Caesar, 'http_get')
        self.caesar_post_mock = caesar_post_patch.start()
        self.caesar_put_mock = caesar_put_patch.start()
        self.caesar_get_mock = caesar_get_patch.start()
        self.addCleanup(caesar_post_patch.stop)
        self.addCleanup(caesar_get_patch.stop)
        self.addCleanup(caesar_put_patch.stop)

    def test_save_to_caesar_update(self):
        workflow = Workflow(1)
        workflow.save_to_caesar()

        self.caesar_put_mock.assert_called_once()
        self.caesar_put_mock.assert_called_with('workflows/1', json={
            'workflow': {
                'id': workflow.id,
                'public_extracts': False,
                'public_reductions': False
            }
        })

    def test_save_to_caesar_create(self):
        self.caesar_get_mock.side_effect = PanoptesAPIException("Couldn't find Workflow with 'id'=1")

        workflow = Workflow(1)
        workflow.save_to_caesar()

        self.caesar_post_mock.assert_called_once()
        self.caesar_post_mock.assert_called_with('workflows', json={
            'workflow': {
                'id': workflow.id,
                'public_extracts': False,
                'public_reductions': False
            }
        })

    def test_save_to_caesar_raises_err(self):
        self.caesar_get_mock.side_effect = PanoptesAPIException("Some other error not workflow_id missing error")

        with self.assertRaises(PanoptesAPIException):
            workflow = Workflow(1)
            workflow.save_to_caesar()

        self.caesar_post_mock.assert_not_called()
        self.caesar_put_mock.assert_not_called()

    def test_caesar_subject_extracts(self):
        workflow = Workflow(1)
        workflow.caesar_subject_extracts(1234)

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/extractors/all/extracts', params={'subject_id': 1234})

    def test_caesar_subject_reductions_get_all_reductions(self):
        workflow = Workflow(1)
        workflow.caesar_subject_reductions(1234)

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subjects/1234/reductions')

    def test_caesar_subject_reductions_filter_by_reducer_key(self):
        workflow = Workflow(1)
        workflow.caesar_subject_reductions(1234, 'test_reducer_key')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subjects/1234/reductions?reducer_key=test_reducer_key')

    def test_caesar_extractors(self):
        workflow = Workflow(1)
        workflow.caesar_extractors()

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/extractors')

    def test_caesar_reducers(self):
        workflow = Workflow(1)
        workflow.caesar_reducers()

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/reducers')

    def test_caesar_rules_subject_rules(self):
        workflow = Workflow(1)
        workflow.caesar_rules('subject')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subject_rules')

    def test_caesar_rules_user_rules(self):
        workflow = Workflow(1)
        workflow.caesar_rules('user')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/user_rules')

    def test_caesar_effects_subject_rule_effects(self):
        workflow = Workflow(1)
        workflow.caesar_effects('subject', 123)

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subject_rules/123/subject_rule_effects')

    def test_caesar_effects_user_rule_effects(self):
        workflow = Workflow(1)
        workflow.caesar_effects('user', 123)
        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/user_rules/123/user_rule_effects')

    def test_add_caesar_extractor_valid_extractor(self):
        workflow = Workflow(1)
        workflow.add_caesar_extractor('external', 'alice')

        self.caesar_post_mock.assert_called_with(f'workflows/{workflow.id}/extractors', json={
            'extractor': {
                'type': 'external',
                'key': 'alice',
                'task_key': 'T0'
            }
        })

    def test_add_caesar_extractor_invalid_extractor(self):
        with self.assertRaises(ValueError) as extractor_error:
            workflow = Workflow(1)
            workflow.add_caesar_extractor('invalid_extractor_type', 'invalid')

        self.caesar_post_mock.assert_not_called()
        self.assertEqual('Invalid extractor type',
                         str(extractor_error.exception))

    def test_add_caesar_reducer_valid_reducer(self):
        workflow = Workflow(1)
        workflow.add_caesar_reducer('count', 'count_key')

        self.caesar_post_mock.assert_called_with(f'workflows/{workflow.id}/reducers', json={
            'reducer': {
                'type': 'count',
                'key': 'count_key'
            }
        })

    def test_add_caesar_reducer_invalid_reducer(self):
        with self.assertRaises(ValueError) as invalid_reducer_err:
            workflow = Workflow(1)
            workflow.add_caesar_reducer('invalid_reducer_type', 'key')

        self.caesar_post_mock.assert_not_called()
        self.assertEqual('Invalid reducer type', str(
            invalid_reducer_err.exception))

    def test_add_caesar_rule_valid_rule_type(self):
        workflow = Workflow(1)
        condition_string = '["gte", ["lookup", "complete.0", 0], ["const", 3]]'
        workflow.add_caesar_rule(condition_string, 'subject')

        self.caesar_post_mock.assert_called_with(f'workflows/{workflow.id}/subject_rules', json={
            'subject_rule': {
                'condition_string': condition_string
            }
        })

    def test_add_caesar_rule_invalid_rule_type(self):
        with self.assertRaises(ValueError) as invalid_rule_type_err:
            workflow = Workflow(1)
            condition_string = '["gte", ["lookup", "complete.0", 0], ["const", 3]]'
            invalid_rule_type = 'invalid_type'
            workflow.add_caesar_rule(condition_string, invalid_rule_type)

        self.caesar_post_mock.assert_not_called()
        expected_message = f'Invalid rule type: {invalid_rule_type}. Rule types can either be by "subject" or "user"'
        self.assertEqual(expected_message, str(invalid_rule_type_err.exception))

    def test_add_caesar_rule_effect_valid_effect(self):
        workflow = Workflow(1)
        retire_reason = {
            'reason': 'other'
        }
        workflow.add_caesar_rule_effect('subject', 12, 'retire_subject', retire_reason)
        expected_endpoint = f'workflows/{workflow.id}/subject_rules/{12}/subject_rule_effects'
        self.caesar_post_mock.assert_called_with(expected_endpoint, json={
            'subject_rule_effect': {
                'action': 'retire_subject',
                'config': retire_reason
            }
        })

    def test_add_caesar_rule_effect_invalid_effect(self):
        with self.assertRaises(ValueError) as invalid_effect_err:
            workflow = Workflow(1)
            workflow.add_caesar_rule_effect('subject', 12, 'promote_user', {'some': 'config'})

        self.caesar_post_mock.assert_not_called()
        self.assertEqual('Invalid action for rule type', str(invalid_effect_err.exception))
