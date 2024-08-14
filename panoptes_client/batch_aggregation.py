from panoptes_client.panoptes import Panoptes, PanoptesAPIException


class BatchAggregation(object):

    def get_aggregations(self, workflow_id):
        return Panoptes.client().get(f'/aggregations?workflow_id={workflow_id}')

    def get_aggregation(self, agg_id):
        return Panoptes.client().get(f'/aggregations/{agg_id}')

    def create_aggregation(self, payload):
        return Panoptes.client().post(f'/aggregations', json=payload)

    def delete_aggregation(self, agg_id, etag):
        return Panoptes.client().delete(f'/aggregations/{agg_id}', etag=etag)

    def fetch_and_delete_aggregation(self, agg_id):
        try:
            single_agg = self.get_aggregation(agg_id)
            self.delete_aggregation(agg_id, single_agg[1])
        except PanoptesAPIException as err:
            raise err

    def run_aggregation(self, payload, delete_if_exists):
        try:
            # if exists and delete_if_exists, delete the first
            response = self.get_aggregations(payload["aggregations"]["links"]["workflow"])
            if response and response[0]:
                has_agg = len(response[0]['aggregations']) > 0
                if delete_if_exists and has_agg:
                    agg_id = response[0]['aggregations'][0]['id']
                    # delete
                    self.fetch_and_delete_aggregation(agg_id)
                    # create
                    return self.create_aggregation(payload)[0]
                elif not has_agg:
                    return self.create_aggregation(payload)[0]
                else:
                    return response[0]
            else:
                self.create_aggregation(payload)[0]
        except PanoptesAPIException as err:
            raise err
