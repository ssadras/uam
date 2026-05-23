"""Configuration for the Docker-sandboxed JAM example.

This config exercises the Docker feature against a curated set of
submissions ranging from a correct reference solution to actively
malicious code (infinite loop, memory hog, network calls,
host-filesystem probes).

WARNING
-------
Several submissions under ``submissions/`` are intentionally hostile
to whichever environment they run in. Do **not** invoke the test
runner against this config unless Docker is installed and
``docker_enabled = True``.

Usage::

    docker pull openjdk:11-slim
    python3 test_runner.py jam/docker_examples/config.py

After the run, each ``submissions/*/A1`` directory should contain a
``result.json`` written by the in-container test driver.

Unlike the standard JAM example, this one does *not* depend on JUnit
or the JAM jars: it ships a self-contained Java test driver
([tests/TestSolution.java](./tests/TestSolution.java)) that talks to
the student's ``a1soln.Solution`` class directly. That keeps the
example reproducible against a vanilla ``openjdk:11-slim`` image with
no network access inside the container.
"""

import os


# ---- PARALLELISM / TIMEOUTS ---- #

# Keep the pool small: each worker may start a heavy JVM-in-container.
max_processes = 4

# Host-side per-command timeout. Must be >= docker_timeout so the
# Docker-internal timeout fires first on a misbehaving submission.
timeout = 120


def timeout_operation():
    """Drop a marker file the grader can grep for."""
    open('timedout', 'w').close()


# ---- STUDENT DIRECTORIES ---- #

students_fname = os.path.join('jam', 'docker_examples', 'directories.txt')


# ---- PRE / POST AMBLE (host-side) ---- #

_EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_DRIVER = os.path.join(_EXAMPLES_DIR, 'tests', 'TestSolution.java')

# Stage the test driver into each student's directory.
preamble_cmd = 'cp {driver} .'.format(driver=_TEST_DRIVER)

# Inside the sandbox container: compile both the student class and
# the test driver, then run the driver. The driver writes result.json.
test_cmd = [
    'javac a1soln/Solution.java TestSolution.java && '
    'java -cp . TestSolution'
]

# Clean up build artefacts so re-runs start fresh. `TestSolution$*.class`
# matches the inner-class .class files javac emits for the test driver's
# private interface and inner records.
postamble_cmd = (
    'rm -f TestSolution.java && '
    "find . -maxdepth 2 -name '*.class' -delete"
)


# ---- DOCKER SANDBOX ---- #

docker_enabled = True
docker_image = 'openjdk:11-slim'

# Resource caps. The JVM is hungrier than CPython, so memory is bumped
# from the framework default of 256m to 512m. Each cap is above what
# the correct submission needs but below what the matching malicious
# submission tries to consume.
docker_cpus = '1.0'
docker_memory = '512m'        # tripped by memhog (allocates ~1 GiB)
docker_disk = '2g'            # JVM + classes need a bit more rootfs
docker_timeout = 60           # tripped by infloop
docker_network = 'none'       # tripped by the network probe
docker_drop_capabilities = True
docker_workdir = '/submission'


# ---- AGGREGATION / TEMPLATING ---- #

uam_dir = os.path.abspath(os.path.join(_EXAMPLES_DIR, '..', '..'))
template_dir = os.path.join(uam_dir, 'templates')
