import os

# ---- TIMEOUT ---- #

# The maximum number of subprocesses to run at any given time.
max_processes = 5

# The maximum time any subprocess should run, in seconds, and an operation
# to be performed when a timeout occurs.
# Make sure this is >> than the individual test timeouts
#   (see pam.py and utils/defaults.py).
timeout = 100
timeout_operation = lambda: open('timedout', 'w').close()


# ---- STUDENT PROCESSING ---- #

# File containing a list of student directories to test.
# -- Each directory should be on its own line.
# -- Each entry should be a relative path from the directory
#     that contains test_runner.py.
students_fname = os.path.join('pam', 'examples', 'directories.txt')

# absolute path to uam
path_to_uam = 'YOUR_PATH_TO_UAM'

# Shell command to be performed before executing tests in a directory or None.
# -- This command will be invoked from within the student's directory!
# -- Notice the use of absolute paths here.
preamble_cmd = ('''cp %s .; cp %s .; cp %s .''' %
                (os.path.join(path_to_uam, 'pam', 'examples', 'test_asst.py'),
                 os.path.join(path_to_uam, 'pam', 'examples', 'test_2_asst.py'),
                 os.path.join(path_to_uam, 'pam', 'examples', 'pep8.py')))

# List of shell commands that execute the tests in a student's
#    submission directory.
# Warning: Some versions of shell don't like the >& redirect, so it's safer
# to redirect stdout and then use 2>&1
# See pam.py for more documentation.
test_cmd = [('%s result.json test_asst.py test_2_asst.py' %
             os.path.join(path_to_uam, 'pam', 'pam.py'))]

# Shell command to be performed after executing tests in a student's submission
#   directory or None.
postamble_cmd = 'rm -rf __pycache__ test_asst.py test_2_asst.py pep8.py'


# ---- DOCKER SANDBOXING (optional) ---- #
# When docker_enabled is True, each test_cmd runs inside a disposable
# Docker container with the student's directory mounted read-write. This
# isolates malicious or runaway student code from the host. Preamble and
# postamble commands still run on the host.
#
# Any of the docker_* settings below may be omitted; defaults come from
# utils/defaults.py.

docker_enabled = False
# docker_image = 'python:3.11-slim'   # image used to run student code
# docker_cpus = '1.0'                 # fractional CPU cores
# docker_memory = '256m'              # memory cap (Docker suffixes)
# docker_disk = '1g'                  # rootfs cap; storage-driver dependent
# docker_timeout = 60                 # per-command wall-clock in seconds
# docker_network = 'none'             # 'none' isolates from the network
# docker_drop_capabilities = True     # drop ALL caps + no-new-privileges
# docker_workdir = '/submission'      # mount point inside the container
# docker_binary = 'docker'            # override if docker is not on PATH


# ---- AGGREGATION AND TEMPLATING ---- #

# where are the templates? absolute path.
template_dir = os.path.join(path_to_uam, 'templates')
