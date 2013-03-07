#!/bin/bash

DIRNAME=/path/to/yearofthebay
lockfile=/tmp/yotb-worker-$1.lock

if (set -o noclobber && echo "$$" > "$lockfile") 2> /dev/null; then
  trap 'rm -rf "$lockfile"; echo $?' INT TERM EXIT

  python $DIRNAME/worker/run.py

  rm -f "$lockfile"
  trap - INT TERM EXIT
fi

