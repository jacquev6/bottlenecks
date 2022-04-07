# Copyright 2022 Vincent Jacques

FROM ubuntu:20.04

# System packages
RUN set -x \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
      make g++ `# Build tools` \
 && apt-get clean
