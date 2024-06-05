
import pytest
from zambeze.campaign.activities import TransferActivity

@pytest.mark.unit
def test_transfer_activity_globus_parsing():

    source_uuid = "11111111-1111-1111-1111-111111111111"
    dest_uuid = "22222222-2222-2222-2222-222222222222"

    trans = TransferActivity(
        name="Test Transfer from A to B",
        source_target=f"globus://{source_uuid}/root1/next1/next2/filename",
        dest_directory=f"globus://{dest_uuid}/root2/next3/dirname",
        override_existing=False,
    )

    assert trans.type == "TRANSFER"
    assert trans.source_target is not None
    assert trans.dest_directory is not None
    assert trans.override_existing is False

    assert len(trans.activity_id) == 36



