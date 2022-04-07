#!/usr/bin/env python

# Copyright 2022 Vincent Jacques

import setuptools


setuptools.setup(
    name="bottlenecks",
    version="0.0.1",
    author="Vincent Jacques",
    author_email="vincent@vincent-jacques.net",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jacquev6/bottlenecks",
    packages=["bottlenecks"],
    install_requires=open("requirements.txt").readlines(),
)
