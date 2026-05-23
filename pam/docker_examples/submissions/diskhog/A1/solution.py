"""Malicious submission: writes a huge file to the container's rootfs.

Verifies that ``docker_disk`` caps disk writes before the host fills
up. ``docker_disk`` is enforced via *two* Docker flags:

  * ``--storage-opt size=``  caps the writable rootfs layer, but only
    on storage drivers that support per-container quotas. The default
    overlay2-on-ext4 and the rootless ``overlayfs`` driver silently
    ignore it.
  * ``--ulimit fsize=``      caps the size of any single file via
    ``RLIMIT_FSIZE`` and is enforced by the kernel regardless of
    storage driver.

Because we write one large file, the ulimit half catches us on every
storage driver: the ``write()`` returns ``EFBIG`` once the file size
hits the cap. On drivers that support it, the storage-opt cap fires
in parallel as the rootfs layer fills.

Why ``/tmp`` and not the working directory?
-------------------------------------------
The submission directory is a bind mount, so writes there pass
straight through to the host filesystem and are not covered by
``--storage-opt size=`` at all. ``/tmp`` inside the container lives on
the container's writable rootfs, which is what the storage-opt cap
applies to.

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
