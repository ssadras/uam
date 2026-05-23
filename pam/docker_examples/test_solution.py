"""Self-contained UAM test driver for the Docker sandbox example.

This script is staged into each student's submission directory by the
preamble command, then executed inside the sandbox container. It runs a
fixed spec against ``solution.py`` and writes a UAM-compatible
``result.json``.

It deliberately depends on the Python standard library only, so the
example works with a plain ``python:3.11-slim`` image with no
additional packages installed inside the container.

Spec under test
---------------
``solution.safe_sum(nums)``      -> int. Sum of integers in ``nums``.
``solution.safe_average(nums)``  -> float. Mean of ``nums``; ``0.0`` if empty.

Both functions are expected to be total (no exceptions on valid input).
"""

import json
import os
import sys
import traceback


# Test spec: (test_id, callable, expected). The callable receives the
# student's `solution` module and returns the value to compare.
SPEC = [
    ('test_sum_empty',     lambda s: s.safe_sum([]),          0),
    ('test_sum_one',       lambda s: s.safe_sum([42]),        42),
    ('test_sum_many',      lambda s: s.safe_sum([1, 2, 3, 4]), 10),
    ('test_sum_negatives', lambda s: s.safe_sum([-1, 1, -2, 2]), 0),
    ('test_avg_empty',     lambda s: s.safe_average([]),       0.0),
    ('test_avg_one',       lambda s: s.safe_average([10]),     10.0),
    ('test_avg_many',      lambda s: s.safe_average([2, 4, 6]), 4.0),
]


def _empty_result():
    return {
        'students': [],
        'results': {},
        'date': 'N/A',
        'assignment': 'N/A',
        'tests': [test_id for test_id, _, _ in SPEC],
    }


def _record(results, test_class, bucket, test_id, payload):
    results.setdefault(test_class, {}).setdefault(bucket, {})[test_id] = payload


def run():
    result = _empty_result()

    try:
        import solution  # noqa: E402 -- imported from cwd
    except Exception:
        # Importing the student file itself crashed (e.g. SyntaxError).
        # Record every spec entry as an error and bail out.
        details = traceback.format_exc()
        for test_id, _, _ in SPEC:
            _record(result['results'], 'docker_examples.SolutionTests',
                    'errors', test_id, {
                        'description': 'Importing solution.py',
                        'message': 'Could not import solution module.',
                        'details': details,
                    })
        return result

    for test_id, call, expected in SPEC:
        try:
            actual = call(solution)
        except Exception as exc:
            _record(result['results'], 'docker_examples.SolutionTests',
                    'errors', test_id, {
                        'description': test_id,
                        'message': '{}: {}'.format(type(exc).__name__, exc),
                        'details': traceback.format_exc(),
                    })
            continue

        if actual == expected:
            _record(result['results'], 'docker_examples.SolutionTests',
                    'passes', test_id, test_id)
        else:
            _record(result['results'], 'docker_examples.SolutionTests',
                    'failures', test_id, {
                        'description': test_id,
                        'message': 'expected {!r}, got {!r}'.format(
                            expected, actual),
                        'details': '',
                    })

    return result


def main():
    target = os.environ.get('UAM_RESULT_JSON', 'result.json')
    payload = run()
    with open(target, 'w') as fp:
        json.dump(payload, fp, indent=2)
    # Exit non-zero if any test errored or failed, so the test runner
    # can flag the run as abnormal.
    for test in payload['results'].values():
        if test.get('errors') or test.get('failures'):
            sys.exit(1)


if __name__ == '__main__':
    main()
