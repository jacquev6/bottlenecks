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
calibration_files := $(patsubst programs/%.cpp,build/%.calibrated-size.txt,$(source_files))
experiment_files := $(patsubst programs/%.cpp,build/%.results.txt,$(source_files))

###############################
# Secondary top-level targets #
###############################

.PHONY: report
report: run
	rm -f build/*.png
	./bottlenecks.py report $(experiment_files) build

.PHONY: run
run: $(experiment_files)

build/%.results.txt: build/%.calibrated-size.txt
	@mkdir -p $(dir $@)
	./bottlenecks.py run $(if $(quick),--max-parallelism 4) build/$* $$(cat $^) >$@.tmp
	mv $@.tmp $@

.PHONY: calibrate
calibrate: $(calibration_files)

build/%.calibrated-size.txt: build/%
	@mkdir -p $(dir $@)
	./bottlenecks.py calibrate $(if $(quick),--target-duration 4) $^ >$@.tmp
	mv $@.tmp $@

.PHONY: build
build: $(binary_files)

build/%: programs/%.cpp
	@mkdir -p $(dir $@)
	g++ -std=c++17 -Wall -Wextra -pedantic -fopenmp -O3 $^ -o $@
