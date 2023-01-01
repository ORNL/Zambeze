#!/bin/bash

set -x
ssh-add
tmux new-session -d -s zsglobus;

tmux split-window -h;
tmux split-window -v;

tmux send -t 0 'ssh z1' ENTER;
tmux send -t 0 'killall nats-server' ENTER;
tmux send -t 0 'nats-server -DV' ENTER;

tmux send -t 1 'ssh cades@ci-datafed-globus1' ENTER;
tmux send -t 1 'rm -f ~/.zambeze/logs/*' ENTER;
tmux send -t 1 'zambeze agent stop && zambeze agent start' ENTER;

tmux send -t 2 'ssh z3' ENTER;
tmux send -t 2 'cd ~/zambeze/examples' ENTER;
tmux send -t 2 'python3 example.py' ENTER;

tmux a -t zsglobus;
 
