FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    less \
    sudo \
  && rm -rf /var/lib/apt/lists/*

COPY ./entrypoint.sh  /

ENTRYPOINT ["/entrypoint.sh"]
