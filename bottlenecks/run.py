# Copyright 2022 Vincent Jacques

import logging
from typing import Any, List, Dict, Optional

import dataclasses
import resource
import subprocess
import time

import psutil



@dataclasses.dataclass
class MonitoredInstantRunMetrics:
    iteration: int
    cpu_percent: float
    user_time: float
    system_time: float
    memory: psutil._pslinux.pfullmem
    io: psutil._pslinux.pio
    context_switches: psutil._common.pctxsw


@dataclasses.dataclass
class MonitoredProcess:
    psutil_process: psutil.Process
    pid: int
    command: List[str]
    spawned_at_iteration: int
    children: List["MonitoredProcess"]
    instant_metrics: List[MonitoredInstantRunMetrics]
    terminated_at_iteration: Optional[int]


@dataclasses.dataclass
class InstantRunMetrics:
    timestamp: float
    cpu_percent: float
    user_time: float
    system_time: float
    memory: Dict
    io: Dict
    context_switches: Dict


@dataclasses.dataclass
class Process:
    command: List[str]
    spawned_at: float
    terminated_at: float
    duration: float
    instant_metrics: List[InstantRunMetrics]
    children: List["Process"]


@dataclasses.dataclass
class MainProcess(Process):
    user_time: float
    system_time: float
    minor_page_faults: int
    major_page_faults: int
    input_blocks: int
    output_blocks: int
    voluntary_context_switches: int
    involuntary_context_switches: int


class Runner:
    def __init__(self, interval=0.1):
        self.__interval = interval

    def run(self, *args, **kwds):
        return self.__Run(self.__interval, *args, **kwds)()

    class __Run:
        def __init__(self, interval, *args, **kwds):
            self.__interval = interval
            self.__args = args
            self.__kwds = kwds

            self.__usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
            self.__iteration = 0
            self.__monitored_processes = {}
            self.__usage_after = None

        def __call__(self):
            main_process = psutil.Popen(*self.__args, **self.__kwds)
            spawn_time = time.perf_counter()
            main_process = self.__start_monitoring_process(main_process)

            while main_process.psutil_process.returncode is None:
                self.__iteration += 1
                try:
                    timeout = spawn_time + self.__iteration * self.__interval - time.perf_counter()
                    assert timeout > 0, "Monitoring is too slow, try increasing the monitoring interval"
                    main_process.psutil_process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Main process is still running
                    self.__run_monitoring_iteration()
                else:
                    # Main process has terminated
                    self.__terminate()

            return self.__return_main_process(main_process)

        def __start_monitoring_process(self, psutil_process):
            psutil_process.cpu_percent()  # Ignore first, meaningless 0.0 returned, as per https://psutil.readthedocs.io/en/latest/#psutil.Process.cpu_percent
            child = MonitoredProcess(
                psutil_process=psutil_process,
                pid=psutil_process.pid,
                command=psutil_process.cmdline(),
                spawned_at_iteration=self.__iteration,
                children=[],  # We'll detect children in the next iteration
                instant_metrics=[],  # We'll gather the first instant metrics in the next iteration
                terminated_at_iteration=None,
            )
            self.__monitored_processes[psutil_process.pid] = child
            parent = psutil_process.ppid()
            if parent in self.__monitored_processes:
                self.__monitored_processes[parent].children.append(child)
            return child

        def __run_monitoring_iteration(self):
            for process in list(self.__monitored_processes.values()):
                try:
                    self.__gather_instant_metrics(process)
                    self.__gather_children(process)
                except psutil.NoSuchProcess:
                    self.__stop_monitoring_process(process)

        def __gather_instant_metrics(self, process):
            try:
                with process.psutil_process.oneshot():
                    cpu_times = process.psutil_process.cpu_times()
                    process.instant_metrics.append(MonitoredInstantRunMetrics(
                        iteration=self.__iteration,
                        cpu_percent=process.psutil_process.cpu_percent(),
                        user_time=cpu_times.user,
                        system_time=cpu_times.system,
                        memory=process.psutil_process.memory_full_info(),
                        io=process.psutil_process.io_counters(),
                        context_switches=process.psutil_process.num_ctx_switches(),
                    ))
            except psutil.AccessDenied:
                logging.warn("Exception psutil.AccessDenied occurred; going on anyway")

        def __gather_children(self, process):
            for child in process.psutil_process.children():
                if child.pid not in self.__monitored_processes:
                    self.__start_monitoring_process(child)

        def __stop_monitoring_process(self, process):
            process.terminated_at_iteration = self.__iteration
            del self.__monitored_processes[process.pid]

        def __terminate(self):
            self.__usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            for process in self.__monitored_processes.values():
                if process.terminated_at_iteration is None:
                    process.terminated_at_iteration = self.__iteration

        def __return_main_process(self, process):
            spawned_at = process.spawned_at_iteration * self.__interval
            terminated_at = process.terminated_at_iteration * self.__interval
            return MainProcess(
                command=process.command,
                spawned_at=spawned_at,
                terminated_at=terminated_at,
                duration=terminated_at - spawned_at,
                instant_metrics=self.__return_instant_metrics(process),
                children=[self.__return_process(child) for child in process.children],
                # According to https://manpages.debian.org/bullseye/manpages-dev/getrusage.2.en.html,
                # we don't care about these fields:
                #   ru_ixrss ru_idrss ru_isrss ru_nswap ru_msgsnd ru_msgrcv ru_nsignals
                # And as 'subprocess' uses fork, ru_maxrss often measures the memory usage of the Python
                # interpreter, so we don't care about that field either.
                user_time=self.__usage_after.ru_utime - self.__usage_before.ru_utime,
                system_time=self.__usage_after.ru_stime - self.__usage_before.ru_stime,
                minor_page_faults=self.__usage_after.ru_minflt - self.__usage_before.ru_minflt,
                major_page_faults=self.__usage_after.ru_majflt - self.__usage_before.ru_majflt,
                input_blocks=self.__usage_after.ru_inblock - self.__usage_before.ru_inblock,
                output_blocks=self.__usage_after.ru_oublock - self.__usage_before.ru_oublock,
                voluntary_context_switches=self.__usage_after.ru_nvcsw - self.__usage_before.ru_nvcsw,
                involuntary_context_switches=self.__usage_after.ru_nivcsw - self.__usage_before.ru_nivcsw,
            )

        def __return_instant_metrics(self, process):
            return [
                InstantRunMetrics(
                    timestamp=m.iteration * self.__interval,
                    cpu_percent=m.cpu_percent,
                    user_time=m.user_time,
                    system_time=m.system_time,
                    memory=m.memory._asdict(),
                    io=m.io._asdict(),
                    context_switches=m.context_switches._asdict(),
                )
                for m in process.instant_metrics
            ]

        def __return_process(self, process):
            spawned_at = process.spawned_at_iteration * self.__interval
            terminated_at = process.terminated_at_iteration * self.__interval
            return Process(
                command=process.command,
                spawned_at=spawned_at,
                terminated_at=terminated_at,
                duration=terminated_at - spawned_at,
                instant_metrics=self.__return_instant_metrics(process),
                children=[self.__return_process(child) for child in process.children],
            )
