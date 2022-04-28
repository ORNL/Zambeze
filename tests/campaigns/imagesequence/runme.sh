#!/bin/bash

# Need ImageMagick installed. On RHEL / CentOS: sudo yum install ImageMagick

convert -delay 20 -loop 0 *.jpg a.gif

