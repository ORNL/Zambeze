FROM python:slim

RUN apt-get update && apt-get install -y imagemagick rsync openssh-server \
    keychain
# The following tools are only useful for debugging/development.
RUN apt-get install -y procps vim iputils-ping curl keychain
#RUN apt-get install -y xz-utils build-essential tcl
# Add a default non root user
RUN useradd --user-group --system --create-home --no-log-init -ms /bin/bash zambeze
# The folder /var/run/sshd is needed to run sshd in the background
RUN mkdir /srv/shared /var/run/sshd  && chown -R zambeze /srv/shared && chmod 777 /srv/shared

WORKDIR /zambeze
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . . 
RUN pip install -e .

ENTRYPOINT ["/zambeze/deployment/scripts/entrypoint.sh", "-c", "--"]
WORKDIR /home/zambeze
USER zambeze
EXPOSE 22
