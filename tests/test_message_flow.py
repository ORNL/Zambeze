import pytest
from zambeze import Campaign, ShellActivity
from zambeze.campaign.activities.dag import DAG


@pytest.mark.unit
def test_message_creation_from_campaign():  # noqa: C901
    """
    Unit test the hypothetical flow of a message from a user's creation through a user
    retrieving a result.
    """

    # Let's pretend these are our agents...
    origin_agent_id = "origin_agent_id_1"
    # running_agents = ["running_agent_1", "running_agent_2"]

    # Create a campaign and add
    campaign = Campaign("My ImageMagick Campaign")

    # define an activity
    curr_dir = "foobar"
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"local://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    """
    *** PHASE 1: Creating an activity initializes properly ***
    """
    assert activity.name == "ImageMagick"
    assert len(activity.files) == 10
    assert activity.command == "convert"
    assert isinstance(activity, ShellActivity)

    assert len(activity.activity_id) == 36
    held_activity_id = activity.activity_id  # hold this out, we'll use later.
    #  assert len(activity.message_id) == 36  # TODO???

    # Agent ID must be none because we don't have one until we flush to agent process.
    # Campaign ID must be none because we have not run campaign.add_activity()

    assert activity.origin_agent_id is None
    assert len(activity.running_agent_ids) == 0
    assert isinstance(activity.running_agent_ids, list)

    """
    *** PHASE 2: Creating DAG from activity works properly ***
    """
    campaign.add_activity(activity)
    internal_dag = campaign._pack_dag_for_dispatch()
    assert isinstance(internal_dag, DAG)

    # Tests to ensure DAG has proper structure.
    # --> should be monitor, ACTIVITY, terminator
    assert len(internal_dag.nodes) == 3

    monitor_node = None
    activity_node = None
    terminator_node = None

    # Note, we have to unpack as generator and can't do simple list access w/ DAGs
    i = 0
    for node in internal_dag.nodes(data=True):
        if i == 0:
            monitor_node = node
        elif i == 1:
            activity_node = node
        elif i == 2:
            terminator_node = node
        i += 1

    # Ensure that the 'identifier' of each dag activity is correct.
    assert monitor_node[0].startswith("MONITOR")
    assert activity_node[0] == held_activity_id
    assert terminator_node[0].startswith("TERMINATOR")

    # And that predecessors and successors appear properly.
    assert len(monitor_node[1]["predecessors"]) == 0
    assert monitor_node[1]["successors"][0] == held_activity_id
    assert activity_node[1]["predecessors"][0] == "MONITOR"
    assert activity_node[1]["successors"][0] == "TERMINATOR"
    assert terminator_node[1]["predecessors"][0] == held_activity_id
    assert len(terminator_node[1]["successors"]) == 0

    # Make sure that the underlying activity objects are also correct.
    assert isinstance(
        monitor_node[1]["activity"], str
    )  # monitor and terminator are string
    assert isinstance(terminator_node[1]["activity"], str)
    assert isinstance(activity_node[1]["activity"], ShellActivity)
    assert "transfer_tokens" in activity_node[1]
    assert "transfer_params" in activity_node[1]

    # Sanity check: added agent_id still in activity
    assert len(activity_node[1]["activity"].activity_id) == 36
    assert activity_node[1]["activity"].origin_agent_id is None

    # Ensure we are properly serialized as a bytestring.
    # internal_serialized_dag = campaign._serialize_dag(internal_dag)
    internal_serialized_dag = internal_dag.serialize_dag()
    assert isinstance(internal_serialized_dag, bytes)

    """
    *** PHASE 3: Send via ZMQ to local message handler. ***
    """

    deserialized_dag = DAG.deserialize_dag(internal_serialized_dag)
    assert isinstance(deserialized_dag, DAG)

    # See if we can access "all_activities"
    for node in deserialized_dag.nodes(data=True):
        if node[0] == "MONITOR":
            node[1]["all_activity_ids"] = deserialized_dag.get_node_ids()
            assert len(node[1]["all_activity_ids"]) == 3

    # UPDATE THE ORIGIN AGENT AND CONFIRM...
    for node in deserialized_dag.nodes(data=True):
        node[1]["origin_agent_id"] = origin_agent_id

    # Just a quick sanity check to ensure everything placed correctly.
    for node in deserialized_dag.nodes(data=True):
        assert node[1]["origin_agent_id"] == origin_agent_id

    serialized_act_nodes = []
    for node in deserialized_dag.nodes(data=True):
        serialized_node = deserialized_dag.serialize_node(node[0])
        assert isinstance(serialized_node, bytes)
        serialized_act_nodes.append(serialized_node)

    """
    *** PHASE 4: receive activities in running agent's message handler.
    """
    deserialized_nodes = []
    for s_node in serialized_act_nodes:
        deserialized_node = DAG.deserialize_node(s_node)
        assert isinstance(deserialized_node, tuple)
        assert isinstance(deserialized_node[0], str)
        assert isinstance(deserialized_node[1], dict)
        deserialized_nodes.append(deserialized_node)

    """
    *** PHASE 5: ensure all 'SHELL' pieces are present and pack result.
    """

    found_activity_node = False
    for node in deserialized_nodes:
        if node[0] == held_activity_id:
            found_activity_node = True
            activity = node[1]["activity"]
            assert isinstance(activity, ShellActivity)
            # assert activity.command == "convert"
            assert activity.type == "SHELL"
            assert activity.campaign_id is not None
            assert len(activity.arguments) == 6
            assert len(activity.files) == 10

            # Now what happens in plugins.py?
            assert activity.plugin_args["shell"] == "bash"
            assert activity.plugin_args["parameters"]["command"] == "convert"
    if not found_activity_node:
        raise ValueError("ACTIVITY NODE NOT FOUND!")

    # Now let's assume we have some sort of result to pack into activity.
    activity.result = {"foo": "magoo"}

    """ PHASE 6: ensure that the result is present. """
    assert isinstance(activity.result, dict)
