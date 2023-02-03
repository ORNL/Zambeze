#!/bin/bash

SCRIPT=$(realpath "$0")
SOURCE=$(dirname "$SCRIPT")
source ${SOURCE}/common.sh

# Start the zambeze agent in the background and display log file content
echo "[zambeze_agent1_start.sh] Home is: $HOME"
USER=$(whoami)
echo "[zambeze_agent1_start.sh] User is: $USER"
HOSTNAME=$(hostname)
echo "[zambeze_agent1_start.sh] Hostname is: $HOSTNAME"
LOG_PATH="$HOME/.zambeze/logs/"
mkdir -p $LOG_PATH

zambeze agent start

expected_foreign_keys=1
ssh_setup

# Check that log entries exist
while [ ! "$(ls -A $LOG_PATH)" ]
do
  sleep 1
  echo "Waiting for log generation..."
done

tail -f $LOG_PATH`ls -t $LOG_PATH | head -n 1`
