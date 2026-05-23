"""Malicious submission: tries to make outbound network calls.

Verifies that ``docker_network = 'none'`` prevents student code from
exfiltrating data or contacting external hosts.

With Docker enabled and the default network mode, the socket call
below should fail almost immediately with EHOSTUNREACH / EAI_AGAIN
because the container has no network interfaces beyond loopback. The
``solution`` module then surfaces that failure as an OSError, which
the test driver records under the 'errors' bucket -- the test_runner
itself remains healthy.
"""

import socket


_DEFAULT_TARGETS = [
    ('example.com', 80),
    ('1.1.1.1', 53),
]


def _try_connect(targets=_DEFAULT_TARGETS):
    last_err = None
    for host, port in targets:
        try:
            with socket.create_connection((host, port), timeout=2) as sock:
                sock.sendall(b'GET / HTTP/1.0\r\n\r\n')
                return sock.recv(64)
        except OSError as err:
            last_err = err
    raise OSError('all network targets unreachable: {}'.format(last_err))


def safe_sum(nums):
    _try_connect()
    return 0


def safe_average(nums):
    _try_connect()
    return 0.0
