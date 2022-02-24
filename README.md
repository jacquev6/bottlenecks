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

Report
======

## Duration *vs.* parallelism

This graph shows the duration of each program according to the number of threads used to run it.
Durations are normalized to the single-thread duration.

The thin dashed lines are representations of [Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law) for $p$ varying from 10% to 100%.

![Duration vs. parallelism](build/duration-vs-parallelism.png)

You should see that `cpu-multiplication` follows Amdahl's law closely, for $p$=100%.
