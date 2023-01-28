FROM python:3.9-slim

RUN apt-get update && apt-get install -y imagemagick rsync openssh-server \
    keychain sudo
# The following tools are only useful for debugging/development.
RUN apt-get install -y procps vim iputils-ping curl keychain dnsutils
#RUN apt-get install -y xz-utils build-essential tcl
# Add a default non root user, with passwordless sudo access
RUN useradd --user-group --system --create-home --no-log-init -ms /bin/bash \
  zambeze && \
  echo "zambeze ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
# The folder /var/run/sshd is needed to run sshd in the background
RUN mkdir /srv/shared /var/run/sshd  && chown -R zambeze /srv/shared && chmod 777 /srv/shared

WORKDIR /home/zambeze
USER zambeze
ENV HOME /home/zambeze
ENV PATH="${PATH}:/home/zambeze/.local/bin"

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . . 
RUN sudo chown -R zambeze /home/zambeze/
RUN pip install --user -e .

ENTRYPOINT ["/home/zambeze/deployment/scripts/entrypoint.sh", "-c", "--"]
EXPOSE 22
