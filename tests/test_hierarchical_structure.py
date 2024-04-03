import pytest
from zambeze import ShellActivity
from zambeze.campaign.activities.abstract_activity import Activity


@pytest.mark.unit
def test_shell_activity_is_activity():
    activity = ShellActivity(
        name="Simple activity ", files=[], command="echo", arguments=["hello"],
    )

    assert isinstance(activity, ShellActivity)
    assert isinstance(activity, Activity)
