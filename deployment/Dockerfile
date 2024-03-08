# Build an image with this Docker file
# docker build --tag zambeze --file deployment/Dockerfile .
#
# Run a container from the image
# docker run --rm -it zambeze /bin/bash

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    imagemagick \
    rsync \
    openssh-server \
    keychain

WORKDIR /home/zambeze
ENV HOME /home/zambeze
ENV PATH="${PATH}:/home/zambeze/.local/bin"

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . . 
RUN pip install .

EXPOSE 22
