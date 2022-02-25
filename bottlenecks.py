#!/usr/bin/env python3

# Copyright 2022 Vincent Jacques

from typing import List

import dataclasses
import json
import logging
import multiprocessing
import os
import resource
import subprocess
import textwrap
import time

import click
import psutil


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
    logging.basicConfig(level=logging.INFO)

    size = 0.5
    duration = 0
    while duration < target_duration:
        lo_size = size
        size *= 2
        duration = run_monitored([program, str(int(size))], 1, warn_about_accuracy=False).clock_duration_s
    hi_size = size
    while abs(duration - target_duration) / target_duration > tolerance:
        size = (lo_size + hi_size) / 2
        duration = run_monitored([program, str(int(size))], 1, warn_about_accuracy=False).clock_duration_s
        if duration > target_duration:
            hi_size = size
        else:
            lo_size = size
    logging.info(f"Duration reached: {duration:.2f}s, relative error: {abs(duration - target_duration) / target_duration:.2f}")
    print(int(size))


@main.command()
@click.argument("program")
@click.argument("size")
@click.option("--min-parallelism", default=1)
@click.option("--max-parallelism", default=int(1.5 * multiprocessing.cpu_count()))
def run(program, size, min_parallelism, max_parallelism):
    logging.basicConfig(level=logging.INFO)

    for parallelism in range(min_parallelism, max_parallelism + 1):
        result = run_monitored([program, size], parallelism)
        print(json.dumps(dataclasses.asdict(result)))


def run_monitored(command, parallelism, warn_about_accuracy=True):
    logging.debug(f"Running {command} with {parallelism} threads")

    instant_metrics = MonitoredRunInstantMetrics(
        timestamps=[],
        cpu_percent=[],
    )
    interval = 0.1
    iteration = 1

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)

    time_before = time.perf_counter()
    process = psutil.Popen(
        command,
        env=dict(os.environ, OMP_NUM_THREADS=str(parallelism)),
    )

    start_time = time.perf_counter()

    process.cpu_percent()  # Ignore first, meaningless 0.0 returned, as per https://psutil.readthedocs.io/en/latest/#psutil.Process.cpu_percent

    while process.returncode is None:
        try:
            process.communicate(timeout=start_time + iteration * interval - time.perf_counter())
        except subprocess.TimeoutExpired:
            now = time.perf_counter() - start_time
            iteration += 1
            logging.debug(f"{command} is still running after {now:.4f}s")
            try:
                with process.oneshot():
                    instant_metrics.cpu_percent.append(process.cpu_percent())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                logging.INFO("Exception (psutil.AccessDenied, psutil.NoSuchProcess) happened")
                instant_metrics.cpu_percent[:] = instant_metrics.cpu_percent[:len(instant_metrics.timestamps)]
            else:
                instant_metrics.timestamps.append(now)
        else:
            time_after = time.perf_counter()

    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)


    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)

    clock_duration_s = time_after - time_before
    if clock_duration_s > 1:
        logging.info(f"Running {command} with {parallelism} threads took {clock_duration_s:.2f}s")
    elif warn_about_accuracy:
        logging.warning(f"Running {command} with {parallelism} threads took {clock_duration_s:.2f}s. This is too quick to guaranty accurate measurements")

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
        instant_metrics=instant_metrics,
    )


@dataclasses.dataclass
class MonitoredRunInstantMetrics:
    timestamps: List[float]
    cpu_percent: List[float]


@dataclasses.dataclass  # @todo (Python >= 3.10) Use `kw_only`
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
    instant_metrics: MonitoredRunInstantMetrics


@main.command()
@click.argument("file-names", nargs=-1)
def report(file_names):
    logging.basicConfig(level=logging.ERROR)

    import matplotlib.pyplot as plt  # Don't import at top-level because:
    # - it's quite long
    # - it calls a subprocess during initialization, which polutes resource.getrusage
    # - logging.basicConfig must be called before importing, to silence a warning

    results_by_program = {}
    for file_name in file_names:
        program = os.path.basename(file_name).split(".")[0]
        with open(file_name) as f:
            results_by_parallelism = {}
            results_by_program[program] = results_by_parallelism
            for line in f:
                result = MonitoredRunResult(**json.loads(line))
                result = dataclasses.replace(result, instant_metrics=MonitoredRunInstantMetrics(**result.instant_metrics))
                results_by_parallelism[result.parallelism] = result

    all_parallelisms = sorted(set(k for d in results_by_program.values() for k in d.keys()))

    make_figure_something_vs_parallelism(
        results_by_program,
        "Duration (normalized)",
        lambda program, parallelism: results_by_program[program][parallelism].clock_duration_s / results_by_program[program][min(results_by_program[program].keys())].clock_duration_s,
        "build/duration-vs-parallelism.png",
        grid=False,
        additional_plots=[
            ((
                all_parallelisms,
                [1 - p + p / parallelism for parallelism in all_parallelisms],
                "--",
            ), dict(
                linewidth=0.5,
                color="grey",
            ))
            for p in (
                (n + 1) / 10
                for n in range(10)
            )
        ]
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "User time (s)",
        lambda program, parallelism: results_by_program[program][parallelism].user_time_s,
        "build/user-time-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "System time (s)",
        lambda program, parallelism: results_by_program[program][parallelism].system_time_s,
        "build/system-time-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Page faults",
        lambda program, parallelism: results_by_program[program][parallelism].minor_page_faults + results_by_program[program][parallelism].major_page_faults,
        "build/page-faults-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Page faults (/s)",
        lambda program, parallelism: (results_by_program[program][parallelism].minor_page_faults + results_by_program[program][parallelism].major_page_faults) / results_by_program[program][parallelism].clock_duration_s,
        "build/page-faults-per-sec-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Outputs (blocks)",
        lambda program, parallelism: results_by_program[program][parallelism].output_blocks,
        "build/outputs-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Outputs (blocks/s)",
        lambda program, parallelism: results_by_program[program][parallelism].output_blocks / results_by_program[program][parallelism].clock_duration_s,
        "build/outputs-per-sec-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Context switches",
        lambda program, parallelism: results_by_program[program][parallelism].involuntary_context_switches + results_by_program[program][parallelism].voluntary_context_switches,
        "build/context-switches-vs-parallelism.png",
    )

    make_figure_something_vs_parallelism(
        results_by_program,
        "Context switches (/s)",
        lambda program, parallelism: (results_by_program[program][parallelism].involuntary_context_switches + results_by_program[program][parallelism].voluntary_context_switches) / results_by_program[program][parallelism].clock_duration_s,
        "build/context-switches-per-sec-vs-parallelism.png",
    )

    cpu_fig, cpu_axes = plt.subplots(len(results_by_program), figsize=(8, 3 * len(results_by_program)), layout="constrained")

    for program_index, (program, results_by_parallelism) in enumerate(results_by_program.items()):
        cpu_ax = cpu_axes[program_index]
        for parallelism, result in results_by_parallelism.items():
            cpu_ax.set_title(f"{program}")
            cpu_ax.plot(
                result.instant_metrics.timestamps,
                result.instant_metrics.cpu_percent,
                "-o",
                label=f"{parallelism} threads",
            )

    for cpu_ax in cpu_axes:
        cpu_ax.set_xlabel("Time (s)")
        cpu_ax.set_ylabel("CPU usage (%)")
        cpu_ax.set_xlim(left=0)
        cpu_ax.set_ylim(bottom=0)
        cpu_ax.grid()
        cpu_ax.legend()
    cpu_fig.savefig("build/instant-cpu-usage.png", dpi=300)


def make_figure_something_vs_parallelism(
    results_by_program,
    something_label,
    main_plot,
    file_name,
    *,
    additional_plots=[],
    grid=True,
):
    import matplotlib.pyplot as plt

    all_parallelisms = sorted(set(k for d in results_by_program.values() for k in d.keys()))

    fig, ax = plt.subplots(figsize=(8, 6), layout="constrained")

    for (args, kwds) in additional_plots:
        ax.plot(*args, **kwds)

    for program, results_by_parallelism in results_by_program.items():
        parallelisms = sorted(results_by_parallelism.keys())
        ax.plot(
            parallelisms,
            [
                main_plot(program, parallelism)
                for parallelism in parallelisms
            ],
            "-o",
            label=f"{program}",
        )

    ax.set_xlabel("Parallelism")
    ax.set_ylabel(something_label)
    ax.set_xlim(left=1, right=max(all_parallelisms))
    ax.set_ylim(bottom=0)
    if grid:
        ax.grid()
    ax.legend()
    fig.savefig(file_name, dpi=300)


if __name__ == "__main__":
    main()
