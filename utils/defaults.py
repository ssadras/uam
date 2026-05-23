DEFAULT_TEMPLATE_TYPE = 'txt'
DEFAULT_AGGREGATE_TEMPLATE = 'aggregated.tpl'
DEFAULT_INDIVIDUAL_TEMPLATE = 'individual.tpl'
DEFAULT_JINJA_EXTENSIONS = ['jinja2.ext.do']
DEFAULT_TEMPLATE_DIR = 'templates'
DEFAULT_REPORT_NAME = 'report'
DEFAULT_IN_JSON_FILE = 'result.json'
DEFAULT_OUT_JSON_FILE = 'aggregated.json'

DEFAULT_TIMEOUT = 2
DEFAULT_VERBOSITY = 2

# ---- DOCKER SANDBOXING ---- #
# Defaults applied when a config does not override them. See
# utils/docker_runner.py for the surrounding logic and README.md for usage.

# Docker is opt-in: a config must set docker_enabled = True to activate it.
DEFAULT_DOCKER_ENABLED = False

# Image used to run student code. Override per-language as needed (e.g.
# 'openjdk:11-slim' for jam, 'python:3.11-slim' for pam).
DEFAULT_DOCKER_IMAGE = 'python:3.11-slim'

# Resource limits applied to every test container.
#   cpus     -- fractional CPU cores (Docker --cpus, e.g. '1.0', '0.5').
#   memory   -- memory cap with Docker suffix ('256m', '1g').
#   disk     -- rootfs size cap (Docker --storage-opt size). Requires a
#               storage driver that supports it (overlay2 on xfs+pquota,
#               devicemapper, btrfs). Ignored when unsupported.
#   timeout  -- per-command wall-clock limit in seconds, enforced by the
#               host via subprocess timeout AND by Docker via --stop-timeout
#               so a hung container is forcibly killed.
DEFAULT_DOCKER_CPUS = '1.0'
DEFAULT_DOCKER_MEMORY = '256m'
DEFAULT_DOCKER_DISK = '1g'
DEFAULT_DOCKER_TIMEOUT = 60

# Path inside the container where the student directory is mounted.
DEFAULT_DOCKER_WORKDIR = '/submission'

# Network mode for the container. 'none' isolates student code from the
# network entirely; switch to 'bridge' only if tests legitimately need it.
DEFAULT_DOCKER_NETWORK = 'none'

# Whether to drop all Linux capabilities and disable privilege escalation.
# Strongly recommended; only disable if tests require elevated privileges.
DEFAULT_DOCKER_DROP_CAPABILITIES = True

# Path to the docker CLI binary. Override if docker lives outside PATH.
DEFAULT_DOCKER_BINARY = 'docker'
