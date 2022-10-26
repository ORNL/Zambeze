# Container Execution

The commands in this document assume you are in the root directory of this
 repository.

### Image building


```shell
$> docker build -t zambeze/zambeze -f deployment/Dockerfile .
```

### Docker compose

The compose file will launch a nats-server container and two containers for 
Zambeze agents, zambeze_agent1 and zambeze_agent2. 
Agent1 is idle, listening to the MQ and, the other is stopped waiting to be
 executed using the API.

```shell
$> docker compose -f deployment/compose.yml down  && docker compose -f deployment/compose.yml up
```