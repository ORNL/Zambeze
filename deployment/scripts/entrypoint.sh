#!/bin/bash

/usr/sbin/sshd

echo "Arguments are"
echo "$@"
if [[ $# -gt 2 ]]
  # Explanation
  # "-" - means start the shell as a login shell
  # "zambeze" - enter as the "zambeze" user
  # "--session-command" - get rid of annoying warning about no job control
  #then su - "zambeze" "$@"
  #else su - "zambeze" --session-command "/bin/bash"
  then exec "$@"
  else exec "/bin/bash"
fi

