Whole-run metrics
=================

This section presents metrics about the whole run of each program, *e.g.* its duration, the total count of its I/Os, the total number of page faults, *etc.*

Duration *vs.* parallelism
--------------------------

Probably the most intuitive metric, this graph shows the duration of each program according to the number of threads used to run it.
Durations are normalized to the single-thread duration.

The thin dashed lines are representations of [Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law) for $p$ (the parallel portion) varying from 10% to 100%.

The left-side graph is just a zoomed view of the other graph, for low parallelisms.

![Duration vs. parallelism](duration-vs-parallelism.png)

System and user times vs. parallelism
-------------------------------------

![User time vs. parallelism](user-time-vs-parallelism.png)

![System time vs. parallelism](system-time-vs-parallelism.png)

Page faults vs. parallelism
---------------------------

![Page faults vs. parallelism](page-faults-vs-parallelism.png)

![Page faults per second vs. parallelism](page-faults-per-sec-vs-parallelism.png)

Outputs vs. parallelism
-----------------------

![Outputs vs. parallelism](outputs-vs-parallelism.png)

![Outputs per second vs. parallelism](outputs-per-sec-vs-parallelism.png)

Context switches vs. parallelism
--------------------------------

![Context switches vs. parallelism](context-switches-vs-parallelism.png)

![Context switches per second vs. parallelism](context-switches-per-sec-vs-parallelism.png)

Instant metrics
===============

This section presents metrics recording all along during the execution, like instant CPU usage or output rate.

CPU usage
---------

![CPU usage](instant-cpu-usage.png)

Memory usage
------------

![Memory usage](instant-memory-usage.png)

Outputs
-------

![Outputs](instant-outputs.png)
