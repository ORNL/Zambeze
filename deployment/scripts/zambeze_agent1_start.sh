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

zambeze2_ip=$(nslookup zambeze2 | grep -A1 zambeze2 | grep Address | awk '{print $2}')
#export ZAMBEZE_CI_TEST_RSYNC_IP="$zambeze2_ip"
#export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY="/home/zambeze/.ssh/id_rsa"
ls -la /etc | grep profile
sudo grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze2_ip" /etc/profile || \
  echo "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze2_ip" | \
  sudo tee /etc/profile
sudo grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" \
  /etc/profile || echo \
  "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" | \
  sudo tee /etc/profile
grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze2_ip" /home/zambeze/.bashrc \
  || echo "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze2_ip" >> /home/zambeze/.bashrc
grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" \
  /home/zambeze/.bashrc || echo \
  "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" >> /home/zambeze/.bashrc

tail -f $LOG_PATH`ls -t $LOG_PATH | head -n 1`
