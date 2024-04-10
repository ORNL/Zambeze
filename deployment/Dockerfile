# Build an image with this Docker file
# docker build --tag zambeze --file deployment/Dockerfile .
#
# Run a container from the image
# docker run --rm -it zambeze /bin/bash

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    imagemagick \
    rsync \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/zambeze

ENV HOME /home/zambeze
ENV PATH="${PATH}:/home/zambeze/.local/bin"

COPY . .

RUN pip install --upgrade pip \
    pip install .[dev]
