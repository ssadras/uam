"""Malicious submission: probes for host filesystem access.

Verifies that:

  * the only host path inside the container is the bind-mounted
    submission directory (so reading /etc/shadow off the host is
    impossible -- the container's /etc/shadow is the *image's*,
    which never contains real credentials);
  * dropped capabilities + ``no-new-privileges`` block privilege
    escalation attempts;
  * writes outside the bind mount land in the ephemeral container
    rootfs and are discarded with ``--rm`` at container exit.

Nothing in this script can damage the host. It is included so graders
can confirm the sandbox behaves as advertised by inspecting the
recorded errors.
"""

import os


_PROBES = [
    '/etc/shadow',          # would-be host credentials (not present)
    '/proc/1/environ',      # init's environment
    '/proc/self/maps',      # leaks ASLR / loaded libs
    '/root/.ssh/id_rsa',    # would-be host ssh key
]


def _read_probes():
    findings = []
    for path in _PROBES:
        try:
            with open(path, 'rb') as fp:
                findings.append((path, len(fp.read(512))))
        except OSError as err:
            findings.append((path, repr(err)))
    return findings


def _write_outside_mount():
    # Attempt to plant a file outside the bind-mounted /submission.
    # Inside Docker this either fails (read-only rootfs paths) or lands
    # in the ephemeral container layer that --rm discards.
    try:
        with open('/tmp/uam-escape-attempt', 'w') as fp:
            fp.write('this file should never appear on the host')
    except OSError:
        pass


def safe_sum(nums):
    _read_probes()
    _write_outside_mount()
    return 0


def safe_average(nums):
    _read_probes()
    _write_outside_mount()
    return 0.0
