# Container Execution

The commands in this document assume you are in the root directory of this
 repository.

## Image building


```shell
$ docker build -t zambeze/zambeze -f deployment/Dockerfile .
```

## Docker compose

The compose file will launch a nats-server container and two containers for 
Zambeze agents, zambeze_agent1 and zambeze_agent2. 
Agent1 is idle, listening to the MQ and, the other is stopped waiting to be
 executed using the API.

```shell
$ docker compose -f deployment/compose.yml down  && docker compose -f deployment/compose.yml up
```

Go to a different terminal tab and make sure the three containers are running:

```shell
$ docker ps
```

## Running the `imagemagick` simple example.

Enter in the container `zambeze2`:

```shell
$ docker exec -it zambeze2 /bin/bash
```

Go to the `examples` directory:

```
cd /zambeze/examples
```

And run:

```shell
$ python imagemagick_files.py
```

You're supposed to see messages coming in the nats output. And the exepcted
output for this agent is:

```shell
[Zambeze Agent] [INFO] 2022-10-29 12:31:11,533 - Initializing Zambeze Agent...
[Zambeze Agent] [INFO] 2022-10-29 12:31:11,534 - Command: zambeze-agent --log-path /root/.zambeze/logs/2022_10_29-12_31_11_533.log --debug --zmq-heartbeat-port 5556 --zmq-activity-port 5555
[Zambeze Agent] [INFO] 2022-10-29 12:31:11,535 - Started agent with PID: 26
[Zambeze Agent] [DEBUG] 2022-10-29 12:31:11,536 - Adding activity: ImageMagick
[Zambeze Agent] [INFO] 2022-10-29 12:31:11,536 - Number of activities to dispatch: 1
[Zambeze Agent] [DEBUG] 2022-10-29 12:31:11,536 - Running activity: ImageMagick
[Zambeze Agent] [INFO] 2022-10-29 12:31:11,731 - REPLY: b'Agent successfully dispatched task!'
```

You should also see a file `~/a.gif` in both agents' containers (`zambeze1` and 2).

