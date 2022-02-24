#!/usr/bin/env bash
# Copyright 2022 Vincent Jacques

set -o errexit

cd "$(dirname "${BASH_SOURCE[0]}")"

# One can export variables BOTTLENECK_SKIP_* before running this script to skip some parts.
# Useful to spare some time on repeated runs.

if [[ -z $BOTTLENECK_SKIP_BUILDER ]]
then
  id_before=$(docker image inspect bottlenecks-builder -f '{{.Id}}' 2>/dev/null || echo none)

  docker build builder --tag bottlenecks-builder

  id_after=$(docker image inspect bottlenecks-builder -f '{{.Id}}')

  # Force full rebuild when dependencies change
  if [[ $id_before != $id_after ]]
  then
    rm -rf build
  fi
fi

docker run \
  --rm --interactive --tty \
  --user $(id -u):$(id -g) `# Avoid creating files as 'root'` \
  --gpus all \
  --network none `# Ensure the repository is self-contained (except for the "docker build" phase)` \
  --volume "$PWD:/wd" --workdir /wd \
  bottlenecks-builder \
    make "$@" -j1  # No parallelism beside what 'bottlenecks.py' does
