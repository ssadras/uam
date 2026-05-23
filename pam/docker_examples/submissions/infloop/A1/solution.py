"""Malicious submission: safe_sum spins forever.

Verifies that ``docker_timeout`` and the host-level subprocess timeout
together kill the container even when student code refuses to exit.

WARNING: do NOT run the test_runner against this submission without
``docker_enabled = True``. Outside the sandbox this will hang the host
process until the host timeout (config.timeout) finally fires.
"""


def safe_sum(nums):
    while True:
        pass  # spin forever; tests Docker wall-clock + timeout(1) cap


def safe_average(nums):
    return safe_sum(nums)
