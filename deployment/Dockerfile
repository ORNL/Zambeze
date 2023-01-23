FROM python:slim

WORKDIR /zambeze
COPY . . 
RUN pip install -e .

RUN apt-get update && apt-get install -y imagemagick
# The following tools are only useful for debugging/development.
RUN apt-get install -y procps vim iputils-ping curl rsync keychain
#RUN apt-get install -y xz-utils build-essential tcl
