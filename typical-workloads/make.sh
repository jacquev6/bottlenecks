#!/usr/bin/env bash
# Copyright 2022 Vincent Jacques

set -o errexit

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! diff builder/Dockerfile build/Dockerfile >/dev/null 2>&1
then
  rm -rf build
  docker build builder --tag bottlenecks-builder
  mkdir build
  cp builder/Dockerfile build/Dockerfile
fi

docker run \
  --rm --interactive --tty \
  --user $(id -u):$(id -g) `# Avoid creating files as 'root'` \
  --network none `# Ensure the repository is self-contained (except for the "docker build" phase)` \
  --volume "$PWD:/wd" --workdir /wd \
  bottlenecks-builder \
    make "$@"
