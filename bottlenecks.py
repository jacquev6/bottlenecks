#!/usr/bin/env python3

# Copyright 2022 Vincent Jacques

import dataclasses
import json
import logging
import multiprocessing
import os
import resource
import subprocess
import sys
import textwrap
import time

import click


logging.basicConfig(level=logging.INFO)


@click.group()
def main():
    pass


@main.command(help=textwrap.dedent("""\
    Find the value of the positive integer argument to pass to PROGRAM so that its duration is TARGET_DURATION.
    PROGRAM is called repeatedly with different arguments.
    The value that makes it last for about TARGET_DURATION seconds is then printed on the standard output.
"""))
@click.argument("program")
@click.option("--target-duration", show_default=True, default=10, metavar="TARGET_DURATION", help="The target duration, in seconds")
@click.option("--tolerance", show_default=True, default=0.05, metavar="TOLERANCE", help="Stop when duration is within TOLERANCE percents of TARGET_DURATION")
def calibrate(program, target_duration, tolerance):
    size = 0.5
    duration = 0
    while duration < target_duration:
        lo_size = size
        size *= 2
        duration = run_monitored([program, str(int(size))], 1).clock_duration_s
    hi_size = size
    while abs(duration - target_duration) / target_duration > tolerance:
        size = (lo_size + hi_size) / 2
        duration = run_monitored([program, str(int(size))], 1).clock_duration_s
        if duration > target_duration:
            hi_size = size
        else:
            lo_size = size
    logging.info(f"Duration reached: {duration}s, relative error: {abs(duration - target_duration) / target_duration}")
    print(int(size))


@main.command()
@click.argument("program")
@click.argument("size")
@click.option("--min-parallelism", default=1)
@click.option("--max-parallelism", default=int(1.5 * multiprocessing.cpu_count()))
def run(program, size, min_parallelism, max_parallelism):
    for parallelism in range(min_parallelism, max_parallelism + 1):
        result = run_monitored([program, size], parallelism)
        print(json.dumps(dataclasses.asdict(result)))


def run_monitored(command, parallelism):
    logging.debug(f"Running {command} with {parallelism} threads")

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    time_before = time.perf_counter()
    subprocess.run(
        command,
        env=dict(os.environ, OMP_NUM_THREADS=str(parallelism)),
        check=True,
    )
    time_after = time.perf_counter()
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)

    clock_duration_s = time_after - time_before
    logging.info(f"Running {command} with {parallelism} threads took {clock_duration_s:.2f}s")

    return MonitoredRunResult(
        parallelism=parallelism,
        clock_duration_s=clock_duration_s,
        # According to https://manpages.debian.org/bullseye/manpages-dev/getrusage.2.en.html,
        # we don't care about these fields:
        #   ru_ixrss ru_idrss ru_isrss ru_nswap ru_msgsnd ru_msgrcv ru_nsignals
        # And as subprocess uses fork, ru_maxrss often measures the memory usage of the Python
        # interpreter, so we don't care about that field either.
        user_time_s=usage_after.ru_utime - usage_before.ru_utime,
        system_time_s=usage_after.ru_stime - usage_before.ru_stime,
        minor_page_faults=usage_after.ru_minflt - usage_before.ru_minflt,
        major_page_faults=usage_after.ru_majflt - usage_before.ru_majflt,
        input_blocks=usage_after.ru_inblock - usage_before.ru_inblock,
        output_blocks=usage_after.ru_oublock - usage_before.ru_oublock,
        voluntary_context_switches=usage_after.ru_nvcsw - usage_before.ru_nvcsw,
        involuntary_context_switches=usage_after.ru_nivcsw - usage_before.ru_nivcsw,
    )


@dataclasses.dataclass
class MonitoredRunResult:
    parallelism: int
    clock_duration_s: float
    user_time_s: float
    system_time_s: float
    minor_page_faults: int
    major_page_faults: int
    input_blocks: int
    output_blocks: int
    voluntary_context_switches: int
    involuntary_context_switches: int


@main.command()
@click.argument("file-names", nargs=-1)
def report(file_names):
    import matplotlib.pyplot as plt  # Don't import at top-level because:
    # - it's quite long
    # - it calls a subprocess during initialization, which polutes resource.getrusage

    results_by_program = {}
    for file_name in file_names:
        program = os.path.basename(file_name).split(".")[0]
        with open(file_name) as f:
            results_by_parallelism = {}
            results_by_program[program] = results_by_parallelism
            for line in f:
                result = MonitoredRunResult(**json.loads(line))
                results_by_parallelism[result.parallelism] = result

    all_parallelisms = sorted(set(k for d in results_by_program.values() for k in d.keys()))

    duration_fig, duration_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    time_fig, time_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    page_faults_fig, page_faults_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    page_faults_per_sec_fig, page_faults_per_sec_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    io_fig, io_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    io_per_sec_fig, io_per_sec_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    context_switches_fig, context_switches_ax = plt.subplots(figsize=(8, 6), layout="constrained")
    context_switches_per_sec_fig, context_switches_per_sec_ax = plt.subplots(figsize=(8, 6), layout="constrained")

    for n in range(10):
        p = (n + 1) / 10
        duration_ax.plot(
            all_parallelisms,
            [1 - p + p / parallelism for parallelism in all_parallelisms],
            "--",
            linewidth=0.5,
            color="grey",
        )

    for program, results_by_parallelism in results_by_program.items():
        parallelisms = sorted(results_by_parallelism.keys())
        duration_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].clock_duration_s / results_by_parallelism[min(parallelisms)].clock_duration_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        time_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].user_time_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program} user",
        )
        time_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].system_time_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program} system",
        )

        page_faults_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].minor_page_faults
                + results_by_parallelism[parallelism].major_page_faults
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        page_faults_per_sec_ax.plot(
            parallelisms,
            [
                (results_by_parallelism[parallelism].minor_page_faults
                + results_by_parallelism[parallelism].major_page_faults)
                / results_by_parallelism[parallelism].clock_duration_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        io_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].output_blocks
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        io_per_sec_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].output_blocks
                / results_by_parallelism[parallelism].clock_duration_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        context_switches_ax.plot(
            parallelisms,
            [
                results_by_parallelism[parallelism].voluntary_context_switches
                + results_by_parallelism[parallelism].involuntary_context_switches
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

        context_switches_per_sec_ax.plot(
            parallelisms,
            [
                (results_by_parallelism[parallelism].voluntary_context_switches
                + results_by_parallelism[parallelism].involuntary_context_switches)
                / results_by_parallelism[parallelism].clock_duration_s
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

    duration_ax.set_xlabel("Parallelism")
    duration_ax.set_ylabel("Duration (normalized)")
    duration_ax.set_xlim(left=1, right=max(all_parallelisms))
    duration_ax.set_ylim(bottom=0, top=1)
    duration_ax.legend()
    duration_fig.savefig("build/duration-vs-parallelism.png", dpi=300)

    time_ax.set_xlabel("Parallelism")
    time_ax.set_ylabel("Time (s)")
    time_ax.set_xlim(left=1, right=max(all_parallelisms))
    time_ax.set_ylim(bottom=0)
    time_ax.grid()
    time_ax.legend()
    time_fig.savefig("build/times-vs-parallelism.png", dpi=300)

    page_faults_ax.set_xlabel("Parallelism")
    page_faults_ax.set_ylabel("Page faults")
    page_faults_ax.set_xlim(left=1, right=max(all_parallelisms))
    page_faults_ax.set_ylim(bottom=0)
    page_faults_ax.grid()
    page_faults_ax.legend()
    page_faults_fig.savefig("build/page-faults-vs-parallelism.png", dpi=300)

    page_faults_per_sec_ax.set_xlabel("Parallelism")
    page_faults_per_sec_ax.set_ylabel("Page faults (/s)")
    page_faults_per_sec_ax.set_xlim(left=1, right=max(all_parallelisms))
    page_faults_per_sec_ax.set_ylim(bottom=0)
    page_faults_per_sec_ax.grid()
    page_faults_per_sec_ax.legend()
    page_faults_per_sec_fig.savefig("build/page-faults-per-sec-vs-parallelism.png", dpi=300)

    io_ax.set_xlabel("Parallelism")
    io_ax.set_ylabel("Output (blocks)")
    io_ax.set_xlim(left=1, right=max(all_parallelisms))
    io_ax.set_ylim(bottom=0)
    io_ax.grid()
    io_ax.legend()
    io_fig.savefig("build/io-vs-parallelism.png", dpi=300)

    io_per_sec_ax.set_xlabel("Parallelism")
    io_per_sec_ax.set_ylabel("Output (blocks/s)")
    io_per_sec_ax.set_xlim(left=1, right=max(all_parallelisms))
    io_per_sec_ax.set_ylim(bottom=0)
    io_per_sec_ax.grid()
    io_per_sec_ax.legend()
    io_per_sec_fig.savefig("build/io-per-sec-vs-parallelism.png", dpi=300)

    context_switches_ax.set_xlabel("Parallelism")
    context_switches_ax.set_ylabel("Context switches")
    context_switches_ax.set_xlim(left=1, right=max(all_parallelisms))
    context_switches_ax.set_ylim(bottom=0)
    context_switches_ax.grid()
    context_switches_ax.legend()
    context_switches_fig.savefig("build/context-switches-vs-parallelism.png", dpi=300)

    context_switches_per_sec_ax.set_xlabel("Parallelism")
    context_switches_per_sec_ax.set_ylabel("Context switches (/s)")
    context_switches_per_sec_ax.set_xlim(left=1, right=max(all_parallelisms))
    context_switches_per_sec_ax.set_ylim(bottom=0)
    context_switches_per_sec_ax.grid()
    context_switches_per_sec_ax.legend()
    context_switches_per_sec_fig.savefig("build/context-switches-per-sec-vs-parallelism.png", dpi=300)


if __name__ == "__main__":
    main()
