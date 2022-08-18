#!/bin/bash

set -x
ssh-add
tmux new-session -d -s zs;

tmux split-window -h;
tmux split-window -v;

tmux send -t 0 's z1' ENTER;
tmux send -t 0 'nats-server -DV' ENTER;

tmux send -t 1 's z2' ENTER;
tmux send -t 1 'zambeze agent stop && zambeze agent start' ENTER;
tmux send -t 1 'rm -f ~/.zambeze/logs/*' ENTER;
tmux send -t 1 'tail -f ~/.zambeze/logs/*.log' ENTER;

tmux send -t 2 's z3' ENTER;
tmux send -t 2 'cd ~/zambeze/examples' ENTER;
tmux send -t 2 'python example.py' ENTER;

tmux a;
 
