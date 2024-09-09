#!/bin/bash

set -e

if [[ -z "$SRC_DIR" ]]; then
    echo Undefined macro "$SRC_DIR"
    exit 1
fi;

cd "$SRC_DIR"

PATH=$PATH:$SRC_DIR/bin
# If prompt defined drop the user to the prompt
if [[ -n "$PROMPT" ]]; then
    exec bash
    exit 0;
fi;

echo "$@"
# Execute the rest of the commands as is
exec bash -c "$@"
