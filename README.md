<!-- Copyright 2022 Vincent Jacques -->

'bottlenecks' is an attempt to demonstrate the different performance bottlenecks that can appear in computer programs.

It's currently limited to programs running only on a CPU.
GPUs may be added later.

Usage
=====

Run:

    ./make.sh

Then have a look at the "Report" section below.

For quicker iterative work on the scripts: `rm -rf build; ./make.sh quick=1`.

Open questions
==============

- Why does `cpu-multiplication` follow Amdahl's law way better than `cpu-trigonometry`? I would have assumed both are purely compute-bound.
- Would using [`select`](https://linux.die.net/man/2/select)-based non-blocking I/O help saturate the disk's bandwidth with fewer threads in `disk-write`?

Report
======

## Definition of the programs being tested

- `cpu-multiplication` does only floating-point multiplications, using very little memory (a few bytes per thread)
- `cpu-trigonometry` computes cosines and arc-cosines, also using very little memory
- `disk-write` writes 1000 large-ish files on the disk
- `ram-bandwidth-copy` copies a large-ish memory array to another one

## Whole-run metrics

This section presents metrics about the whole run of each program, *e.g.* its duration, the total count of its I/Os, the total number of page faults, *etc.*

### Duration *vs.* parallelism

This graph shows the duration of each program according to the number of threads used to run it.
Durations are normalized to the single-thread duration.

The thin dashed lines are representations of [Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law) for $p$ (the parallel portion) varying from 10% to 100%.

![Duration vs. parallelism](build/duration-vs-parallelism.png)

Observations:
- `cpu-multiplication` follows Amdahl's law closely, for $p$=100%: it's purely compute-bound and does benefit from any additional compute resource... until it reaches the number of physical cores in my processor (14). It looses performance on the 15th thread, when hyperthreading is used, then on the 29th thread when it is greater than the number of hyperthread cores.
- `ram-bandwidth-copy` gains from a second thread, but is quite flat for 3 or more threads: it reaches the RAM's bandwidth and adding compute power doesn't help. It even makes things worse as we can see the duration increasing slowly for 6 threads and more
- `disk-write` follows Amdahl's law closely for $p$=90% until 8 threads, but flattens for 9 threads and more: it reaches the disk's bandwidth

### System and user times vs. parallelism

![User time vs. parallelism](build/user-time-vs-parallelism.png)

![System time vs. parallelism](build/system-time-vs-parallelism.png)

Observations:
- `cpu-multiplication` has zero system time, as expected. Its user time is globally constant because it always does the same computations. It raises slightly because of the overhead of having several threads.
- the effect of the numbers of cores (14 physical, 28 logical) is clearly visible on `ram-bandwidth-copy`'s user time, albeit a bit strange

### Page faults vs. parallelism

![Page faults vs. parallelism](build/page-faults-vs-parallelism.png)

![Page faults per second vs. parallelism](build/page-faults-per-sec-vs-parallelism.png)

### Outputs vs. parallelism

![Outputs vs. parallelism](build/outputs-vs-parallelism.png)

![Outputs per second vs. parallelism](build/outputs-per-sec-vs-parallelism.png)

### Context switches vs. parallelism

![Context switches vs. parallelism](build/context-switches-vs-parallelism.png)

![Context switches per second vs. parallelism](build/context-switches-per-sec-vs-parallelism.png)

## Instant metrics

### CPU usage

![CPU usage](build/instant-cpu-usage.png)
