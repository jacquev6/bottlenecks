# Copyright 2022 Vincent Jacques

############################
# Default top-level target #
############################

.PHONY: default
default: build

#############
# Inventory #
#############

# Source files
source_files := $(wildcard *.cpp)

# Intermediate files
binary_files := $(patsubst %.cpp,build/%,$(source_files))

###############################
# Secondary top-level targets #
###############################

.PHONY: build
build: $(binary_files)

build/%: %.cpp
	@mkdir -p $(dir $@)
	g++ -std=c++17 -Wall -Wextra -pedantic -fopenmp -O3 $^ -o $@
