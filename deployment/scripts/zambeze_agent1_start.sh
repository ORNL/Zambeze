#!/bin/bash

# Start the zambeze agent in the background and display log file content
LOG_PATH="$HOME/.zambeze/logs/"
mkdir -p $LOG_PATH

zambeze agent start

# Generate ssh keys
ssh-keygen -b 2048 -t rsa -f $HOME/.ssh/id_rsa -q -N ""
cp $HOME/.ssh/id_rsa.pub /srv/shared/id_rsa_zambeze1.pub

while [ ! "$(ls -A /srv/shared/ | grep 'id_rsa_zambeze2.pub' )" ]
do
  sleep 1
  echo "Waiting for zambeze2 ssh public key..."
done

# Register as an authorized host
cat /srv/shared/id_rsa_zambeze2.pub > $HOME/.ssh/authorized_keys
chmod 600 $HOME/.ssh/authorized_keys

# Check that log entries exist
while [ ! "$(ls -A $LOG_PATH)" ]
do
  sleep 1
  echo "Waiting for log generation..."
done

tail -f $LOG_PATH`ls -t $LOG_PATH | head -n 1`
