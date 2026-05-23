"""Malicious submission: writes a huge file to the container's rootfs.

Verifies that ``docker_disk`` (``--storage-opt size=``) caps the
writable layer of the container, killing the process with ENOSPC
before the host fills up.

Why ``/tmp`` and not the working directory?
-------------------------------------------
``--storage-opt size=`` limits the *container's writable rootfs layer*,
not bind-mounted host directories. The student's submission directory
is a bind mount, so writes there bypass ``docker_disk`` and land on
the host disk. ``/tmp`` inside the container, on the other hand, lives
on the container's rootfs and *is* covered by the cap.

For real grading deployments, also place a filesystem quota (XFS
prjquota, ext4 quota, …) on the host directory that holds student
submissions if you want to bound writes to the bind mount too. See
the top-level README for the full discussion.

The write target is sized at 2 GiB, well above the default
``docker_disk = '1g'``. Outside the sandbox this script will fill the
container's rootfs; do not run without ``docker_enabled = True``.
"""

_TARGET = '/tmp/diskhog.bin'
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
