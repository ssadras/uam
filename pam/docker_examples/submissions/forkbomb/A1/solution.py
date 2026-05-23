"""Malicious submission: attempts to exhaust the process table.

Verifies that, with capabilities dropped and CPU/memory caps in place,
the container cannot fork enough children to harm the host. Docker's
default PID namespace also confines any children that *do* get spawned
to the container.

The bomb is intentionally bounded (4096 fork attempts, not unbounded
recursion) so that if someone misruns this example WITHOUT Docker the
host has a fighting chance of recovering. Bounded or not, do not run
this without ``docker_enabled = True``.
"""

import os

_BOUND = 4096


def _bomb():
    spawned = 0
    while spawned < _BOUND:
        try:
            pid = os.fork()
        except OSError:
            # Hit a resource limit -- exactly what we are testing.
            return
        if pid == 0:
            # Child: continue forking, then exit to keep the chain alive
            # without truly exploding.
            spawned += 1
            continue
        spawned += 1


def safe_sum(nums):
    _bomb()
    return 0


def safe_average(nums):
    _bomb()
    return 0.0
