# Copyright 2022 Vincent Jacques

############################
# Default top-level target #
############################

.PHONY: default
default: report

#############
# Inventory #
#############

# Output directory
report_directory?=build/report

# Source files
source_files := $(wildcard programs/*.cpp)

# Intermediate files
binary_files := $(patsubst programs/%.cpp,build/%,$(source_files))
calibration_files := $(patsubst programs/%.cpp,build/%.calibrated-size.txt,$(source_files))
experiment_files := $(patsubst programs/%.cpp,$(report_directory)/%.results.txt,$(source_files))

###############################
# Secondary top-level targets #
###############################

.PHONY: report
report: report_images report_information | $(report_directory)/report.md

$(report_directory)/report.md:
	@mkdir -p $(dir $@)
	cp report.md.tmpl $@

.PHONY: report_images
report_images: $(experiment_files)
	@mkdir -p $(report_directory)
	@rm -f $(report_directory)/*.png
	./bottlenecks.py report $(experiment_files) $(report_directory)

.PHONY: report_information
report_information:
	@mkdir -p $(report_directory)
	lscpu --output-all >$(report_directory)/lscpu.txt
	lsmem --output-all >$(report_directory)/lsmem.txt

.PHONY: run
run: $(experiment_files)

$(report_directory)/%.results.txt: build/%.calibrated-size.txt
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
