FROM python:3.9-slim
RUN  apt-get -yq update && \
     apt-get -yqq install ssh

ARG SSH_KEY
ENV SSH_KEY=$SSH_KEY

# Make ssh dir
RUN mkdir /root/.ssh/
 
# Create id_rsa from string arg, and set permissions

RUN echo "$SSH_KEY" > /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa
 
# Create known_hosts
RUN touch /root/.ssh/known_hosts

# Add git providers to known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts


MAINTAINER "falcoeye team"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update && \
    apt-get install -y git && \
    apt-get -y install ffmpeg libsm6 libxext6 && \
    pip3 install -U pip && \
    pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install gunicorn

EXPOSE 6000

COPY . .

CMD ["gunicorn", "-b 0.0.0.0:6000", "falcoeye:app"]
