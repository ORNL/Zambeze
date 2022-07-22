#!/bin/bash

import subprocess
import sys
import os

my_env = os.environ.copy()
my_env["PATH"] = "$PATH:/opt/homebrew/bin"


cmd_list = ["/opt/homebrew/bin/convert", "-delay", "20", "-loop", "0",
            "/Users/6o1/PycharmProjects/zambeze/examples/../tests/campaigns/imagesequence/*.jpg",
            "a.gif"]
# cmd_list = ["ls", "/Users/6o1/Desktop"]
# cmd_list = ["echo", "$0"]
# cmd_list = ["echo", "hello"]
# cmd_list = "echo $0"
# cmd_list = ["/bin/pwd"]
cmd_list = ["ls", "/opt/homebrew"]

cmd = ' '.join(cmd_list)
with open("/Users/6o1/Desktop/stdout.txt", "w") as out, \
        open("/Users/6o1/Desktop/stderr.txt", "w") as err:
    process = subprocess.Popen(cmd,
                               stdout=out,
                               stderr=err,
                               shell=False,
                               # executable='/bin/bash',
                               env=my_env)


# stdout = process.communicate()[0]
# print('STDOUT:{}'.format(stdout))
# while True:
#   output = process.stdout.readline()