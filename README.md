<!-- Copyright 2022 Vincent Jacques -->

'bottlenecks' is an attempt to demonstrate the different performance bottlenecks that can appear in computer programs.

It's currently limited to programs running only on a CPU.
GPUs may be added later.

Usage
=====

Run:

    ./make.sh

Then have a look at the "Report" section below.

Open questions
==============

- Why does `cpu-multiplication` follow Amdahl's law way better than `cpu-trigonometry`? I would have assumed both are purely compute-bound.
- Would using [`select`](https://linux.die.net/man/2/select)-based non-blocking I/O help saturate the disk's bandwidth with fewer threads in `disk-write`?

Report
======

## Definition of the programs being tested

- `cpu-multiplication` does only floating-point multiplications, using very little memory (a few bytes per thread)
- `cpu-trigonometry` computes cosines and arc-cosines, also using very little memory
- `ram-bandwidth-copy` copies a large-ish memory array to another one

## Duration *vs.* parallelism

This graph shows the duration of each program according to the number of threads used to run it.
Durations are normalized to the single-thread duration.

The thin dashed lines are representations of [Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law) for $p$ (the parallel portion) varying from 10% to 100%.

![Duration vs. parallelism](build/duration-vs-parallelism.png)

On my machine, I can see that:
- `cpu-multiplication` follows Amdahl's law closely, for $p$=100%: it's purely compute-bound and does benefit from any additional compute resource
- `ram-bandwidth-copy` gains from a second thread, but is quite flat for 3 or more threads: it reaches the RAM's bandwidth and adding compute power doesn't help. It even makes things worse as we can see the duration increasing slowly for 6 threads and more
- `disk-write` follows Amdahl's law closely for $p$=90% until 8 threads, but flattens for 9 threads and more: it reaches the disk's bandwidth
