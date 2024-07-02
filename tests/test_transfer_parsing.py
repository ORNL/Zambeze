
import logging
import pytest
from zambeze.campaign.activities import TransferActivity
from zambeze.campaign import Campaign
from zambeze.campaign.activities import dag


@pytest.mark.unit
def test_transfer_activity_globus_parsing():

    # Step 1: instantiate a transfer activity
    source_uuid = "11111111-1111-1111-1111-111111111111"
    dest_uuid = "22222222-2222-2222-2222-222222222222"

    trans = TransferActivity(
        name="Test Transfer from A to B",
        source_target=f"globus://{source_uuid}/root1/next1/next2/filename",
        dest_directory=f"globus://{dest_uuid}/root2/next3/dirname",
        override_existing=False,
    )

    assert trans.activity_type == "TRANSFER"
    assert trans.source_target is not None
    assert trans.dest_directory is not None
    assert trans.override_existing is False

    assert len(trans.activity_id) == 36

    # Step 2: Place TransferActivity into campaign, dispatch as DAG.
    logger = logging.getLogger(__name__)
    campaign = Campaign("My ImageMagick Campaign", logger=logger, force_login=False)
    campaign.add_activity(trans)

    ser_dag = campaign._pack_dag_for_dispatch().serialize_dag()

    # Step 3: deserialize DAG, confirm items still present
    deser_dag = dag.DAG.deserialize_dag(ser_dag)

    # Grab the TransferActivity from the DAG
    transfer_activity = None
    for node in deser_dag.nodes(data=True):
        if isinstance(node[1]['activity'], TransferActivity):
            node[1]["all_activity_ids"] = deser_dag.get_node_ids()
            assert len(node[1]["all_activity_ids"]) == 3
            transfer_activity = node[1]["activity"]

    assert transfer_activity.activity_type == "TRANSFER"
