FROM ubuntu:20.04

# System packages
RUN set -x \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
      python3-pip `# Common tools` \
      make g++ `# Build tools` \
 && apt-get clean

# Python packages
RUN pip3 install \
      click \
      matplotlib \
      psutil
