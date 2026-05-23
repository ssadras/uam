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
    DEFAULT_DOCKER_USER,
    DEFAULT_DOCKER_WORKDIR,
)


# Sentinel string for DEFAULT_DOCKER_USER. Resolved at runtime in
# DockerConfig to the current host UID:GID on POSIX systems, or to None
# (i.e. let the image choose) on non-POSIX hosts.
_HOST_USER_SENTINEL = 'host'


class DockerConfigError(ValueError):
    '''Raised when a config module supplies an invalid Docker setting.'''


# Suffix -> multiplier for Docker-style size strings ('1g', '256m', ...).
_SIZE_UNITS = {
    'b': 1,
    'k': 1024,
    'm': 1024 ** 2,
    'g': 1024 ** 3,
    't': 1024 ** 4,
}


def _parse_size(spec):
    '''Translate a Docker-style size spec to a byte count.

    Accepts ``'1g'``, ``'256M'``, ``'1024k'``, ``'42'`` (bare bytes),
    or already-numeric values. Raises ``DockerConfigError`` on anything
    else.
    '''

    if isinstance(spec, int):
        if spec <= 0:
            raise DockerConfigError(
                'size must be positive (got {!r}).'.format(spec))
        return spec
    if not isinstance(spec, str) or not spec.strip():
        raise DockerConfigError(
            'size must be a non-empty string (got {!r}).'.format(spec))

    text = spec.strip().lower()
    suffix = text[-1]
    if suffix in _SIZE_UNITS:
        digits = text[:-1]
    else:
        digits = text
        suffix = 'b'

    try:
        value = int(digits)
    except ValueError:
        raise DockerConfigError(
            'cannot parse size {!r}; expected forms like '
            "'256m', '1g', '1024k'.".format(spec))
    if value <= 0:
        raise DockerConfigError(
            'size must be positive (got {!r}).'.format(spec))
    return value * _SIZE_UNITS[suffix]


class DockerConfig:
    '''Resolved Docker settings for a single test_runner invocation.

    Attributes mirror the `DEFAULT_DOCKER_*` constants in
    `utils.defaults`. Construct via `DockerConfig.from_module(config)` so
    that missing attributes pick up the framework defaults.

    '''

    def __init__(self, enabled, image, cpus, memory, disk, timeout,
                 workdir, network, drop_capabilities, user, binary):
        self.enabled = bool(enabled)
        self.image = image
        self.cpus = cpus
        self.memory = memory
        self.disk = disk
        self.timeout = int(timeout)
        self.workdir = workdir
        self.network = network
        self.drop_capabilities = bool(drop_capabilities)
        self.user = self._resolve_user(user)
        self.binary = binary

        self._validate()

    @staticmethod
    def _resolve_user(spec):
        '''Translate a `docker_user` config value into a `--user` argument.

        - Falsy values (`None`, `''`) -> no `--user` flag is emitted.
        - The sentinel ``'host'`` -> ``f'{euid}:{egid}'`` on POSIX; ``None``
          on platforms without ``os.geteuid`` (e.g. Windows hosts, where
          Docker Desktop already translates bind-mount ownership).
        - Anything else is passed through unchanged so users can pin a
          specific UID/GID or named user.
        '''

        if not spec:
            return None
        if spec == _HOST_USER_SENTINEL:
            if hasattr(os, 'geteuid') and hasattr(os, 'getegid'):
                return '{}:{}'.format(os.geteuid(), os.getegid())
            return None
        return str(spec)

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
        if self.disk:
            # Validate eagerly so a misconfigured size errors at config
            # load time, not partway into the run.
            _parse_size(self.disk)

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
            user=getattr(config, 'docker_user', DEFAULT_DOCKER_USER),
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
        # Two-pronged disk cap:
        #   * --storage-opt size=<spec>  caps the container's writable
        #     rootfs layer on storage drivers that support per-container
        #     quotas (overlay2 on XFS+pquota, devicemapper, btrfs, zfs).
        #     Other drivers (notably overlay2 on ext4 and the newer
        #     "overlayfs" driver) silently ignore the option.
        #   * --ulimit fsize=<bytes>     caps the maximum size of any
        #     single file the process can create, enforced unconditionally
        #     by the kernel via RLIMIT_FSIZE. This catches single-file
        #     disk-fill attacks even when --storage-opt is ignored.
        # Together they give defense in depth across storage drivers.
        args.extend(['--storage-opt', 'size={}'.format(docker_config.disk)])
        args.extend(['--ulimit',
                     'fsize={}'.format(_parse_size(docker_config.disk))])

    if docker_config.drop_capabilities:
        args.extend([
            '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges',
        ])

    if docker_config.user:
        # Running as the host UID:GID keeps bind-mount permissions sane
        # once CAP_DAC_OVERRIDE has been dropped. It is also a stronger
        # security posture: even if the container is breached, the
        # attacker only has the host user's privileges, not root's.
        args.extend(['--user', docker_config.user])

    # Enforce the wall-clock limit *inside* the container as well: signal
    # propagation from `docker run` to the container is best-effort, and a
    # student process that ignores SIGTERM can otherwise outlive the host
    # subprocess timeout. `timeout --signal=KILL` is part of GNU coreutils
    # and busybox; both are present in any reasonable base image.
    guarded_cmd = 'timeout --signal=KILL {seconds}s {cmd}'.format(
        seconds=docker_config.timeout, cmd=test_cmd)

    args.extend([docker_config.image, 'sh', '-c', guarded_cmd])

    return ' '.join(shlex.quote(arg) for arg in args)
