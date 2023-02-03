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

echo "[zambeze_agent2_start.sh] I'm idle!" & tail -f /dev/null
