# Copyright 2022 Vincent Jacques

FROM ubuntu:20.04

# System packages
RUN set -x \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
      make g++ `# Build tools` \
      software-properties-common wget dirmngr gpg-agent `# Required to install CUDA` \
 && apt-get clean

# CUDA
# Instructions adapted from https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=20.04&target_type=deb_network
RUN set -x \
 && wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin --output-document=/etc/apt/preferences.d/cuda-repository-pin-600 \
 && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub \
 && add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /" \
 && apt-get update \
 && apt-get install --yes \
      cuda-nvcc-11-2 `# Build tools` \
      cuda-cudart-dev-11-2 `# Runtime dependencies` \
 && apt-get clean

ENV PATH="/usr/local/cuda-11.2/bin:${PATH}"
