# Copyright 2022 Vincent Jacques

############################
# Default top-level target #
############################

.PHONY: default
default: report

#############
# Inventory #
#############

# Source files
source_files := $(wildcard programs/*.cpp)

# Intermediate files
binary_files := $(patsubst programs/%.cpp,build/%,$(source_files))
calibration_files := $(patsubst programs/%.cpp,build/%.size,$(source_files))
experiment_files := $(patsubst programs/%.cpp,build/%.json,$(source_files))

###############################
# Secondary top-level targets #
###############################

.PHONY: report
report: run
	./bottlenecks.py report $(experiment_files)

.PHONY: run
run: $(experiment_files)

build/%.json: build/%.size
	@mkdir -p $(dir $@)
	./bottlenecks.py run build/$* $$(cat $^) >$@

.PHONY: calibrate
calibrate: $(calibration_files)

build/%.size: build/%
	@mkdir -p $(dir $@)
	./bottlenecks.py calibrate $^ >$@

.PHONY: build
build: $(binary_files)

build/%: programs/%.cpp
	@mkdir -p $(dir $@)
	g++ -std=c++17 -Wall -Wextra -pedantic -fopenmp -O3 $^ -o $@
