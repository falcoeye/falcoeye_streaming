FROM python:3.9-slim

MAINTAINER "falcoeye team"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update && \
    apt-get -y install ffmpeg libsm6 libxext6 && \
    pip3 install -U pip && \
    pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install gunicorn

EXPOSE 6000

COPY . .

CMD ["gunicorn", "-b 0.0.0.0:6000", "falcoeye:app"]
