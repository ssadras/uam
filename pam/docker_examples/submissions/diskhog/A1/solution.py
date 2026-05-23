"""Malicious submission: writes a huge file to the working directory.

Verifies that ``docker_disk`` (and/or filesystem quota on the bind
mount) prevents student code from filling the host's disk.

The write target is the current working directory, which inside the
container is the bind-mounted submission dir. With the default
``docker_disk = '1g'`` the write should fail well before reaching the
2 GiB cap baked in below.

Without Docker this script will happily fill the host filesystem; do
not run without ``docker_enabled = True``.
"""

_TARGET = 'diskhog.bin'
_CHUNK = b'\x00' * (1024 * 1024)         # 1 MiB
_LIMIT_MIB = 2048                        # write up to 2 GiB and then stop


def _fill_disk():
    written = 0
    with open(_TARGET, 'wb') as fp:
        while written < _LIMIT_MIB:
            fp.write(_CHUNK)
            written += 1


def safe_sum(nums):
    _fill_disk()
    return 0


def safe_average(nums):
    _fill_disk()
    return 0.0
