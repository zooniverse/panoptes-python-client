import unittest
import sys
from panoptes_client.batch_aggregation import BatchAggregation

if sys.version_info <= (3, 0):
    from mock import patch
else:
    from unittest.mock import patch

class TestBatchAggregation(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.mock_client_patch = patch('panoptes_client.panoptes.Panoptes.client')
        self.mock_client = self.mock_client_patch.start()

        self.addCleanup(self.mock_client_patch.stop)

        batch_agg_get_aggregations_patch = patch.object(BatchAggregation, 'get_aggregations')
        fetch_and_delete_aggregation_patch = patch.object(BatchAggregation, 'fetch_and_delete_aggregation')
        create_aggregation_patch = patch.object(BatchAggregation, 'create_aggregation')

        self.batch_agg_get_aggregations_mock = batch_agg_get_aggregations_patch.start()
        self.fetch_and_delete_aggregation_mock = fetch_and_delete_aggregation_patch.start()
        self.create_aggregation_mock = create_aggregation_patch.start()

        self.addCleanup(batch_agg_get_aggregations_patch.stop)
        self.addCleanup(fetch_and_delete_aggregation_patch.stop)
        self.addCleanup(create_aggregation_patch.stop)

        self.payload = {
            "aggregations": {
                "links": {
                    "user": 1,
                    "workflow": 1,
                }
            }
        }

        self.agg_mock_value = [{
            'aggregations': [{
                'id': '1',
                'href': '/aggregations/1',
                'created_at': '2024-08-13T10:26:32.560Z',
                'updated_at': '2024-08-13T10:26:32.576Z',
                'uuid': None,
                'task_id': 'task_id',
                'status': 'pending',
                'links': {'project': '1', 'workflow': '1', 'user': '1'}
            }]
        }, 'etag']

    def test_run_aggregation_with_delete_if_exists(self):
        self.batch_agg_get_aggregations_mock.return_value = self.agg_mock_value

        BatchAggregation().run_aggregation(payload=self.payload, delete_if_exists=True)
        self.fetch_and_delete_aggregation_mock.assert_called_with(self.agg_mock_value[0]['aggregations'][0]['id'])
        self.create_aggregation_mock.assert_called_with(self.payload)

    def test_run_aggregation_with_previously_created_case(self):
        self.batch_agg_get_aggregations_mock.return_value = self.agg_mock_value

        BatchAggregation().run_aggregation(payload=self.payload, delete_if_exists=False)
        self.fetch_and_delete_aggregation_mock.assert_not_called()
        self.create_aggregation_mock.assert_not_called()

    def test_run_aggregation_with_no_previously_created_case(self):
        self.batch_agg_get_aggregations_mock.return_value = [{'aggregations': []}, 'etag']

        BatchAggregation().run_aggregation(payload=self.payload, delete_if_exists=False)
        self.fetch_and_delete_aggregation_mock.assert_not_called()
        self.create_aggregation_mock.assert_called_with(self.payload)
