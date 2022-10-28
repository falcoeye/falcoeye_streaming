FROM ubuntu:20.04

MAINTAINER "falcoeye team"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3
RUN apt install  -y python3-pip
RUN pip3 install --no-cache-dir -r requirements.txt 
RUN pip3 install gunicorn

EXPOSE 6000

COPY . .

CMD ["gunicorn", "-b 0.0.0.0:6000", "falcoeye:app"]