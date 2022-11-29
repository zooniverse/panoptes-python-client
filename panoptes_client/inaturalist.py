from panoptes_client.panoptes import Panoptes


class Inaturalist(object):
    """
    The class that interacts with the Panoptes' iNaturalist functionality.
    Currently, this includes a single route that allows the importing of
    iNaturalist Observations as Zooniverse Subjects.
    """

    def inat_import(
        taxon_id,
        subject_set_id,
        updated_since=None
    ):
        """
        Begins an import of iNaturalist Observations as Zooniverse Subjects.
        Response is a 200 if Panoptes begins the import successfully.
        Requires owner or collaborator access to the subject set's linked project.
        Takes three arguments:
            taxon_id:       the iNat taxon ID of a particular species
            subject_set_id: the Zoo subject set id subjects should be imported into.
                            Updated observations will upsert their respective subjects.
            updated_since:  a date range limiter on the iNat Observations query.
                            Warning: defaults to None and will import ALL Observations
                            by default. This will likely be a lot and take a while.
        Examples::
            # Import gray squirrel observations updated during or after Halloween 2022 to subject set id 3:
            Inaturalist.inat_import(46017, 3, '2022-10-31')

            # Import all royal flycatcher observations to subject set id 4:
            Inaturalist.inat_import(16462, 4)
        """

        return Panoptes.client().post(
            f'/inaturalist/import',
            json={
                'taxon_id': taxon_id,
                'subject_set_id': subject_set_id,
                'updated_since': updated_since
            }
        )
