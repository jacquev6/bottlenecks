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
source_files := $(wildcard *.cpp) $(wildcard *.cu)

# Intermediate files
binary_files := $(patsubst %.cu,build/%,$(patsubst %.cpp,build/%,$(source_files)))

###############################
# Secondary top-level targets #
###############################

.PHONY: build
build: $(binary_files)

build/%: %.cpp
	@mkdir -p $(dir $@)
	g++ -std=c++17 -Wall -Wextra -Werror -pedantic -fopenmp -O3 $^ -o $@

build/%: %.cu
	@mkdir -p $(dir $@)
	nvcc -std=c++17  -Xcompiler -Wall,-Wextra,-Werror -O3 $^ -o $@
