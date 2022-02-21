#!/bin/bash

set -ex

if [[ -z "$UID" ]]; then
    echo Undefined macro $UID
    exit 1
fi;

if [[ -z "$GID" ]]; then
    echo Undefined macro $GID
    exit 1
fi;

if [[ -z "$USERNAME" ]]; then
    echo Undefined macro $USERNAME
    exit 1
fi;

if [[ -z "$SRC_DIR" ]]; then
    echo Undefined macro $SRC_DIR
    exit 1
fi;

addgroup  --gid $GID $USERNAME
useradd --uid $GID --gid $UID $USERNAME -p test

echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/doudalis

cd $SRC_DIR

chown root:root /tmp
chmod a+rwxs /tmp

PATH=$PATH:$SRC_DIR/bin
# If prompt defined drop the user to the prompt
if [[ -n "$PROMPT" ]]; then
    exec gosu $USERNAME bash
    exit 0;
fi;

# Execute the rest of the commands as is
exec gosu $USERNAME bash -c "$@"
