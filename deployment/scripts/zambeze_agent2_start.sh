#!/bin/bash

# Generate ssh keys
ssh-keygen -b 2048 -t rsa -f $HOME/.ssh/id_rsa -q -N ""
# Copy our key to shared path
cp $HOME/.ssh/id_rsa.pub /srv/shared/id_rsa_zambeze2.pub

while [ ! "$(ls -A /srv/shared/ | grep 'id_rsa_zambeze1.pub' )" ]
do
  sleep 1
  echo "Waiting for zambeze1 ssh public key..."
done

# Register as an authorized host
cat /srv/shared/id_rsa_zambeze1.pub > $HOME/.ssh/authorized_keys
chmod 600 $HOME/.ssh/authorized_keys

echo "Im idle!" & tail -f /dev/null
