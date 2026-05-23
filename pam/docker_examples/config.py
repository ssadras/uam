"""Configuration for the Docker-sandboxed PAM example.

This config exercises the Docker feature against a curated set of
submissions ranging from a correct reference solution to actively
malicious code (infinite loop, fork bomb, memory hog, disk hog,
network calls, host-filesystem probes).

WARNING
-------
Several submissions under ``submissions/`` are intentionally hostile
to whichever environment they run in. Do **not** invoke the test
runner against this config unless Docker is installed and
``docker_enabled = True``. The host-side timeout is the only thing
that protects you if you forget; that is not a substitute for the
sandbox.

Usage::

    pip install -r requirements.txt
    docker pull python:3.11-slim
    python3 test_runner.py pam/docker_examples/config.py

After the run, each ``submissions/*/A1`` directory should contain a
``result.json`` written by the in-container test driver.
"""

import os


# ---- PARALLELISM / TIMEOUTS ---- #

# Keep the pool small: each worker may start a heavy container.
max_processes = 4

# Host-side per-command timeout, in seconds. Must be >= docker_timeout
# so the Docker-internal timeout is the one that fires first on a
# misbehaving submission.
timeout = 90


def timeout_operation():
    """Drop a marker file the grader can grep for."""
    open('timedout', 'w').close()


# ---- STUDENT DIRECTORIES ---- #

students_fname = os.path.join('pam', 'docker_examples', 'directories.txt')


# ---- PRE / POST AMBLE (host-side) ---- #

# Stage the test driver into each student's directory so the sandbox
# container can run it from cwd (== bind-mounted /submission).
_EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
_TEST_DRIVER = os.path.join(_EXAMPLES_DIR, 'test_solution.py')

# `cp` works on Linux/macOS; the entire framework is POSIX-only.
preamble_cmd = 'cp {driver} .'.format(driver=_TEST_DRIVER)

# Each test_cmd runs INSIDE the Docker container at the student's
# (bind-mounted) directory. ``test_solution.py`` writes result.json.
test_cmd = ['python3 test_solution.py']

# Clean up the staged driver and any compiled artefacts the in-container
# Python interpreter may have left behind in the bind-mounted directory.
postamble_cmd = 'rm -rf test_solution.py __pycache__'


# ---- DOCKER SANDBOX ---- #

docker_enabled = True
docker_image = 'python:3.11-slim'

# Resource caps. Each is comfortably above what the *correct*
# submission needs, but well below what each malicious submission
# tries to consume.
docker_cpus = '1.0'           # 1 full core
docker_memory = '256m'        # tripped by memhog (allocates ~1 GiB)
docker_disk = '1g'            # tripped by diskhog (writes ~2 GiB)
docker_timeout = 30           # tripped by infloop
docker_network = 'none'       # tripped by the network probe
docker_drop_capabilities = True
docker_workdir = '/submission'


# ---- AGGREGATION / TEMPLATING ---- #

path_to_uam = os.path.abspath(os.path.join(_EXAMPLES_DIR, '..', '..'))
template_dir = os.path.join(path_to_uam, 'templates')
