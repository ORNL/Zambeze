"""These items are required as part of any message

The agent_id must be a valid UUID
The message_id must be a valid UUID
The submission_time must be time in
The type can be either ACTIVITY or STATUS
"""

REQUIRED_GENERAL_COMPONENTS = {
    "origin_agent_id": "",
    "running_agent_ids": [],
    "message_id": "",
    "submission_time": "",
    "type": "",
}
