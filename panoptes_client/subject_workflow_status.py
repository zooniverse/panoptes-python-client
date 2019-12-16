from panoptes_client.panoptes import PanoptesObject


class SubjectWorkflowStatus(PanoptesObject):
    """
    Retrieve SubjectWorkflowStatus responses from Panoptes i.e. the retirement
    status (current state, retirement date, retirement reason) of a
    subject/workflow pair.

    Example use:

    Get the status of a given subject:
        subject_workflow_status = next(
            SubjectWorkflowStatus.where(subject_id='30089908')
        )

    The .where(kwargs) method works with:
    - id (i.e. the id of the SubjectWorkflowStatus, which is *not* the same as
      the subject_id)
    - subject_id
    - workflow_id

    Remember that one subject may be classified on many workflows, and hence
    may have many SubjectWorkflowStatus' (one per subject/workflow pair).
    """
    _api_slug = 'subject_workflow_statuses'
    _edit_attributes = {}
