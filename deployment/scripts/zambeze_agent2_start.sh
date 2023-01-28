#!/bin/bash

SCRIPT=$(realpath "$0")
SOURCE=$(dirname "$SCRIPT")
source ${SOURCE}/common.sh

echo "[zambeze_agent2_start.sh] Home is: $HOME"
USER=$(whoami)
echo "[zambeze_agent2_start.sh] User is: $USER"
HOSTNAME=$(hostname)
echo "[zambeze_agent2_start.sh] Hostname is: $HOSTNAME"

expected_foreign_keys=1
ssh_setup

zambeze1_ip=$(nslookup zambeze1 | grep -A1 zambeze1 | grep Address | awk '{print $2}')
#export ZAMBEZE_CI_TEST_RSYNC_IP="$zambeze1_ip"
#export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY="/home/zambeze/.ssh/id_rsa"
ls -la /etc | grep profile
sudo grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze1_ip" /etc/profile || \
  echo "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze1_ip" | \
  sudo tee /etc/profile
sudo grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" \
  /etc/profile || echo \
  "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" | \
  sudo tee /etc/profile
grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze1_ip" /home/zambeze/.bashrc \
  || echo "export ZAMBEZE_CI_TEST_RSYNC_IP=$zambeze1_ip" >> /home/zambeze/.bashrc
grep -qxF "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" \
  /home/zambeze/.bashrc || echo \
  "export ZAMBEZE_CI_TEST_RSYNC_SSH_KEY=/home/zambeze/.ssh/id_rsa" >> /home/zambeze/.bashrc

echo "[zambeze_agent2_start.sh] I'm idle!" & tail -f /dev/null
