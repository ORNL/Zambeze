#!/bin/bash

sudo /usr/sbin/sshd

echo "[entrypoint.sh] Arguments are: $@"
USER=$(whoami)
echo "[entrypoint.sh] Running as user: $USER"
echo "[entrypoint.sh] Home is: $HOME"
if [[ $# -gt 2 ]]
  then 
    echo "[entrypoint.sh] Running: /bin/bash $@"
    export USER=$USER && export HOME=$HOME && /bin/bash $@
  else
    echo "[entrypoint.sh] Running: /bin/bash"
    export USER=$USER && export HOME=$HOME && /bin/bash
fi

