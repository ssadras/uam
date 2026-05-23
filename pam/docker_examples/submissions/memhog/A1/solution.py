"""Malicious submission: allocates more memory than the container has.

Verifies that ``docker_memory`` kills the process via OOM-killer
before the host's free memory is touched.

The allocation is sized at 1 GiB worth of bytes — well above the
default ``docker_memory = '256m'``. Without Docker this would simply
eat host memory until either the allocation fails or the OS OOM-kills
the process; do not run without ``docker_enabled = True``.
"""


def _eat_memory():
    # Hold references in a list so the garbage collector cannot reclaim,
    # and allocate a *fresh* buffer each iteration. ``bytearray(N)``
    # guarantees a new N-byte allocation; ``b'\x00' * N`` would also
    # allocate, but reusing a cached chunk via ``chunk * 1`` would not
    # (CPython returns the same object for ``bytes * 1``).
    chunks = []
    while len(chunks) <= 64:                       # 64 * 16 MiB = 1 GiB
        chunks.append(bytearray(16 * 1024 * 1024))
    return chunks


def safe_sum(nums):
    _eat_memory()
    return 0


def safe_average(nums):
    _eat_memory()
    return 0.0
