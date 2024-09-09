ARG PARENT_IMAGE=ubuntu_base:ltest
FROM ${PARENT_IMAGE}

RUN apt-get update && apt-get install -y \
    tox \
  && rm -rf /var/lib/apt/lists/*

COPY ./entrypoint.sh  /

ENTRYPOINT ["/entrypoint.sh"]
