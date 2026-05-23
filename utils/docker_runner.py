'''Docker sandbox wrapper for the UAM test runner.

Student-submitted code is untrusted. Running it directly on the grading
host risks data loss, network abuse, and resource exhaustion. This module
builds a `docker run` invocation that wraps an arbitrary shell command in
a disposable container with:

  * a read-write bind mount of the student's submission directory
  * configurable CPU, memory, and disk caps
  * a wall-clock timeout enforced at the Docker level (in addition to the
    subprocess-level timeout already applied by test_runner)
  * network isolation and dropped Linux capabilities by default

The public entry point is `build_docker_command`, which returns a single
shell-quoted string suitable for `subprocess.Popen(..., shell=True)`. This
keeps the call site in test_runner.py untouched aside from a wrapping step.

Configuration is read from a UAM config module via `DockerConfig.from_module`;
missing attributes fall back to the constants in `utils.defaults`.

'''

import os
import shlex
import shutil

from utils.defaults import (
    DEFAULT_DOCKER_BINARY,
    DEFAULT_DOCKER_CPUS,
    DEFAULT_DOCKER_DISK,
    DEFAULT_DOCKER_DROP_CAPABILITIES,
    DEFAULT_DOCKER_ENABLED,
    DEFAULT_DOCKER_IMAGE,
    DEFAULT_DOCKER_MEMORY,
    DEFAULT_DOCKER_NETWORK,
    DEFAULT_DOCKER_TIMEOUT,
    DEFAULT_DOCKER_WORKDIR,
)


class DockerConfigError(ValueError):
    '''Raised when a config module supplies an invalid Docker setting.'''


class DockerConfig:
    '''Resolved Docker settings for a single test_runner invocation.

    Attributes mirror the `DEFAULT_DOCKER_*` constants in
    `utils.defaults`. Construct via `DockerConfig.from_module(config)` so
    that missing attributes pick up the framework defaults.

    '''

    def __init__(self, enabled, image, cpus, memory, disk, timeout,
                 workdir, network, drop_capabilities, binary):
        self.enabled = bool(enabled)
        self.image = image
        self.cpus = cpus
        self.memory = memory
        self.disk = disk
        self.timeout = int(timeout)
        self.workdir = workdir
        self.network = network
        self.drop_capabilities = bool(drop_capabilities)
        self.binary = binary

        self._validate()

    def _validate(self):
        if not self.enabled:
            return  # other fields are unused when Docker is off
        if not self.image:
            raise DockerConfigError('docker_image must be a non-empty string.')
        if self.timeout <= 0:
            raise DockerConfigError(
                'docker_timeout must be a positive integer (got {!r}).'.format(
                    self.timeout))
        if not self.workdir or not self.workdir.startswith('/'):
            raise DockerConfigError(
                'docker_workdir must be an absolute container path '
                '(got {!r}).'.format(self.workdir))

    @staticmethod
    def from_module(config):
        '''Build a DockerConfig from a user-supplied config module.

        Any attribute not present on `config` falls back to the matching
        `DEFAULT_DOCKER_*` constant.

        '''

        return DockerConfig(
            enabled=getattr(config, 'docker_enabled', DEFAULT_DOCKER_ENABLED),
            image=getattr(config, 'docker_image', DEFAULT_DOCKER_IMAGE),
            cpus=getattr(config, 'docker_cpus', DEFAULT_DOCKER_CPUS),
            memory=getattr(config, 'docker_memory', DEFAULT_DOCKER_MEMORY),
            disk=getattr(config, 'docker_disk', DEFAULT_DOCKER_DISK),
            timeout=getattr(config, 'docker_timeout', DEFAULT_DOCKER_TIMEOUT),
            workdir=getattr(config, 'docker_workdir', DEFAULT_DOCKER_WORKDIR),
            network=getattr(config, 'docker_network', DEFAULT_DOCKER_NETWORK),
            drop_capabilities=getattr(
                config, 'docker_drop_capabilities',
                DEFAULT_DOCKER_DROP_CAPABILITIES),
            binary=getattr(config, 'docker_binary', DEFAULT_DOCKER_BINARY),
        )


def is_docker_available(binary=DEFAULT_DOCKER_BINARY):
    '''Return True if `binary` can be located on PATH.

    Resolving the binary up front lets test_runner fail fast with a clear
    message rather than spawning shells that fail one by one.

    '''

    return shutil.which(binary) is not None


def build_docker_command(test_cmd, host_dir, docker_config):
    '''Return a shell command string that runs `test_cmd` inside Docker.

    Parameters
    ----------
    test_cmd : str
        The original shell command to run inside the container. It is
        forwarded verbatim to `sh -c`, so multi-step pipelines and
        redirections behave the same as on the host.
    host_dir : str
        Absolute path on the host that should be bind-mounted into the
        container as the working directory. Typically the student's
        submission directory.
    docker_config : DockerConfig
        Resolved Docker settings.

    Returns
    -------
    str
        A single shell command suitable for `subprocess.Popen(shell=True)`.

    '''

    if not docker_config.enabled:
        raise DockerConfigError(
            'build_docker_command called with docker disabled.')

    host_dir = os.path.abspath(host_dir)
    mount = '{src}:{dst}'.format(
        src=host_dir, dst=docker_config.workdir)

    args = [
        docker_config.binary, 'run',
        '--rm',                                # auto-remove on exit
        '--interactive',                       # propagate stdin/stdout/stderr
        '--workdir', docker_config.workdir,
        '--volume', mount,
        '--network', docker_config.network,
        '--cpus', str(docker_config.cpus),
        '--memory', str(docker_config.memory),
        '--memory-swap', str(docker_config.memory),  # disable swap
        '--stop-timeout', str(docker_config.timeout),
    ]

    if docker_config.disk:
        # --storage-opt size requires a driver that supports per-container
        # quotas. Docker rejects it on unsupported drivers; we surface the
        # error rather than silently dropping the limit.
        args.extend(['--storage-opt', 'size={}'.format(docker_config.disk)])

    if docker_config.drop_capabilities:
        args.extend([
            '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges',
        ])

    # Enforce the wall-clock limit *inside* the container as well: signal
    # propagation from `docker run` to the container is best-effort, and a
    # student process that ignores SIGTERM can otherwise outlive the host
    # subprocess timeout. `timeout --signal=KILL` is part of GNU coreutils
    # and busybox; both are present in any reasonable base image.
    guarded_cmd = 'timeout --signal=KILL {seconds}s {cmd}'.format(
        seconds=docker_config.timeout, cmd=test_cmd)

    args.extend([docker_config.image, 'sh', '-c', guarded_cmd])

    return ' '.join(shlex.quote(arg) for arg in args)
