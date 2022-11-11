FROM python:slim

WORKDIR /zambeze
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . . 
RUN pip3 install .

RUN apt-get update && apt-get install -y imagemagick

# The following tools are only useful for debugging.
RUN apt-get install -y procps vim iputils-ping curl
