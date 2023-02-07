#!/bin/bash

# ssh_setup function
#
# Step 1. Function will generate a ssh rsa key pair for the host
# Step 2. The public key will be placed in the shared folder /srv/shared/
#         folder and given the name id_rsa_{hostname}.pub.
# Step 3. The folder will be checked for any other keys that might exist in
#         /srv/shared and will add them to the authorized keys file
#
# Expected arguments to the function are:
#
# expected_foreign_keys - this variable expects a number to indicate how many
#                         foriegn keys to expect to add as a known host 
ssh_setup() {

  echo "[common.sh] Running processes are:"
  ps aux

  if [ ! -f "$HOME/.ssh/id_rsa" ]
  then
    echo "[common.sh] Missing file $HOME/.ssh/id_rsa generating key pair."
   
    local hostname=$(hostname)
    local my_rsa="id_rsa_${hostname}"
    local my_rsa_pub="id_rsa_${hostname}.pub"
    # Only generate new keys if there are none in /srv/shared
    if [ ! -f "/srv/shared/${my_rsa}" ]
    then
      echo "[common.sh] keys missing from /srv/shared"
      ssh-keygen -b 2048 -t rsa -f $HOME/.ssh/id_rsa -q -N ""
      cp $HOME/.ssh/id_rsa.pub "/srv/shared/${my_rsa_pub}"
      cp $HOME/.ssh/id_rsa "/srv/shared/${my_rsa}"
    else
      echo "[common.sh] keys found in /srv/shared copying to $HOME/.ssh"
      if [ ! -d "/home/zambeze/.ssh" ] 
      then
        echo "[common.sh] Folder missing $HOME/.ssh creating"
        mkdir -p "/home/zambeze/.ssh"
        chmod 700 "/home/zambeze/.ssh"
      fi
      cp "/srv/shared/${my_rsa_pub}" $HOME/.ssh/id_rsa.pub 
      cp "/srv/shared/${my_rsa}" $HOME/.ssh/id_rsa 
    fi

		local num_detected_foreign_keys=$(ls -A -d /srv/shared/* | grep .pub | grep -v ${my_rsa_pub} | wc -l)
		while [ $num_detected_foreign_keys -lt $expected_foreign_keys ]
		do
						echo "[common.sh] Detected ${num_detected_foreign_keys} foreign keys, expected: ${expected_foreign_keys}"
						sleep 1
						num_detected_foreign_keys=$(ls -A -d /srv/shared/* | grep .pub | grep -v ${my_rsa} | wc -l)
		done

		foreign_public_keys=$(ls -A -d /srv/shared/* | grep .pub | grep -v ${my_rsa} )

		# Register as an authorized host
		if [ -f $HOME/.ssh/authorized_keys ]
		then
						echo "[common.sh] Removing authorized keys"
						rm $HOME/.ssh/authorized_keys
		fi

		for foreign_key in ${foreign_public_keys}
		do
						echo "[common.sh] Adding foreign key to authorized keys ${foreign_key}"
						cat ${foreign_key} >> $HOME/.ssh/authorized_keys
		done
		chmod 600 $HOME/.ssh/authorized_keys
    echo "Host *" > $HOME/.ssh/config
    echo "  StrictHostKeyChecking no" >> $HOME/.ssh/config
    echo "  UserKnownHostsFile=/dev/null" >> $HOME/.ssh/config
	fi
}
