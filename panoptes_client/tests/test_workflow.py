import unittest
import sys

if sys.version_info <= (3, 0):
    from mock import patch
else:
    from unittest.mock import patch

from panoptes_client.workflow import Workflow
from panoptes_client.caesar import Caesar


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        super().setUp()
        caesar_post_patch = patch.object(Caesar, 'http_post')
        caesar_get_patch = patch.object(Caesar, 'http_get')
        self.caesar_post_mock = caesar_post_patch.start()
        self.caesar_get_mock = caesar_get_patch.start()
        self.addCleanup(caesar_post_patch.stop)
        self.addCleanup(caesar_get_patch.stop)

    def test_add_to_caesar(self):
        workflow = Workflow(1)
        workflow.add_to_caesar()

        self.caesar_post_mock.assert_called_once()

        self.caesar_post_mock.assert_called_with('workflows', json={
            'workflow': {
                'id': workflow.id
            }
        })

    def test_subject_extracts(self):
        workflow = Workflow(1)
        workflow.subject_extracts(1234)

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/extractors/all/extracts', params={'subject_id': 1234})

    def test_subject_reductions_get_all_reductions(self):
        workflow = Workflow(1)
        workflow.subject_reductions(1234)

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subjects/1234/reductions')

    def test_subject_reductions_filter_by_reducer_key(self):
        workflow = Workflow(1)
        workflow.subject_reductions(1234, 'test_reducer_key')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subjects/1234/reductions?reducer_key=test_reducer_key')

    def test_extractors(self):
        workflow = Workflow(1)
        workflow.extractors()

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/extractors')

    def test_reducers(self):
        workflow = Workflow(1)
        workflow.reducers()

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/reducers')

    def test_rules_subject_rules(self):
        workflow = Workflow(1)
        workflow.rules('subject')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/subject_rules')

    def test_rules_user_rules(self):
        workflow = Workflow(1)
        workflow.rules('user')

        self.caesar_get_mock.assert_called_with(
            f'workflows/{workflow.id}/user_rules')

    def test_add_extractor_valid_extractor(self):
        workflow = Workflow(1)
        workflow.add_extractor('external', 'alice')

        self.caesar_post_mock.assert_called_with(f'workflows/{workflow.id}/extractors', json={
            'extractor': {
                'type': 'external',
                'key': 'alice',
                'task_key': 'T0'
            }
        })

    def test_add_extractor_invalid_extractor(self):
        with self.assertRaises(ValueError) as extractor_error:
            workflow = Workflow(1)
            workflow.add_extractor('invalid_extractor_type', 'invalid')

        self.caesar_post_mock.assert_not_called()
        self.assertEqual('Invalid extractor type',
                         str(extractor_error.exception))

    def test_add_reducer_valid_reducer(self):
        workflow = Workflow(1)
        workflow.add_reducer('count', 'count_key')

        self.caesar_post_mock.assert_called_with(f'workflows/{workflow.id}/reducers', json={
            'reducer': {
                'type': 'count',
                'key': 'count_key'
            }
        })

    def test_add_reducer_invalid_reducer(self):
        with self.assertRaises(ValueError) as invalid_reducer_err:
            workflow = Workflow(1)
            workflow.add_reducer('invalid_reducer_type', 'key')

        self.caesar_post_mock.assert_not_called()
        self.assertEqual('Invalid reducer type', str(
            invalid_reducer_err.exception))
