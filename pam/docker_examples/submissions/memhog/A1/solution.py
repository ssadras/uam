"""Malicious submission: allocates more memory than the container has.

Verifies that ``docker_memory`` kills the process via OOM-killer
before the host's free memory is touched.

The allocation is sized at 1 GiB worth of bytes — well above the
default ``docker_memory = '256m'``. Without Docker this would simply
eat host memory until either the allocation fails or the OS OOM-kills
the process; do not run without ``docker_enabled = True``.
"""


def _eat_memory():
    # Hold references in a list so the garbage collector cannot reclaim.
    chunks = []
    chunk = b'\x00' * (16 * 1024 * 1024)  # 16 MiB
    while True:
        chunks.append(chunk * 1)
        # 64 * 16 MiB = 1 GiB upper bound on this loop.
        if len(chunks) > 64:
            break
    return chunks


def safe_sum(nums):
    _eat_memory()
    return 0


def safe_average(nums):
    _eat_memory()
    return 0.0
