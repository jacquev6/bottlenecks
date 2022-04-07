# Copyright 2022 Vincent Jacques

from typing import Dict, List

import dataclasses
import logging
import resource
import subprocess
import time

import psutil


def run(*args, **kwds):
    instant_metrics = MonitoredRunInstantMetrics(
        timestamps=[],
        cpu_percent=[],
        user_time_s=[],
        system_time_s=[],
        memory=[],
        io=[],
        context_switches=[],
    )
    interval = 0.1
    iteration = 1

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)

    time_before = time.perf_counter()
    process = psutil.Popen(*args, **kwds)

    start_time = time.perf_counter()

    process.cpu_percent()  # Ignore first, meaningless 0.0 returned, as per https://psutil.readthedocs.io/en/latest/#psutil.Process.cpu_percent

    while process.returncode is None:
        try:
            process.communicate(timeout=start_time + iteration * interval - time.perf_counter())
        except subprocess.TimeoutExpired:
            now = time.perf_counter() - start_time
            iteration += 1
            logging.debug(f"{process.cmdline} is still running after {now:.4f}s")
            try:
                with process.oneshot():
                    instant_metrics.cpu_percent.append(process.cpu_percent())
                    cpu_times = process.cpu_times()
                    instant_metrics.user_time_s.append(cpu_times.user)
                    instant_metrics.system_time_s.append(cpu_times.system)
                    instant_metrics.memory.append(process.memory_full_info()._asdict())
                    instant_metrics.io.append(process.io_counters()._asdict())
                    instant_metrics.context_switches.append(process.num_ctx_switches())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                logging.info("Exception (psutil.AccessDenied, psutil.NoSuchProcess) happened")
                instant_metrics.cpu_percent[:] = instant_metrics.cpu_percent[:len(instant_metrics.timestamps)]
                instant_metrics.user_time_s[:] = instant_metrics.user_time_s[:len(instant_metrics.timestamps)]
                instant_metrics.system_time_s[:] = instant_metrics.system_time_s[:len(instant_metrics.timestamps)]
                instant_metrics.memory[:] = instant_metrics.memory[:len(instant_metrics.timestamps)]
                instant_metrics.io[:] = instant_metrics.io[:len(instant_metrics.timestamps)]
                instant_metrics.context_switches[:] = instant_metrics.context_switches[:len(instant_metrics.timestamps)]
            else:
                instant_metrics.timestamps.append(now)
        else:
            time_after = time.perf_counter()

    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)

    clock_duration_s = time_after - time_before

    result = MonitoredRunResult(
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

    return (process, result)


@dataclasses.dataclass
class MonitoredRunInstantMetrics:
    timestamps: List[float]
    cpu_percent: List[float]
    user_time_s: List[float]
    system_time_s: List[float]
    memory: List[Dict]
    io: List[Dict]
    context_switches: List[int]


@dataclasses.dataclass  # @todo (Python >= 3.10) Use `kw_only`
class MonitoredRunResult:
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
