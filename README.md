## UAM

UAM stands for Universal AutoMarker. It is a framework for testing
student assignments written in a variety of programming languages,
collecting the results, and exporting them for easy viewing using
templates.

We currently provide full support for Python (pam) and Java (jam).

We are working on supporting SQL (sqam), Racket (ram), and Haskell
(ham).

We welcome collaboration and contributions!

## Requirements

You need Python >= 3.3 installed on your system. Then, install the
requirements listed in the file requirements.txt. The easiest way to
do this is to use pip (pip3 for Python 3):

`pip install -r /path_to_uam/requirements.txt`

You can use [virtualenv](https://virtualenv.pypa.io) to avoid
installing the packages system-wide.

To use JAM, you also need Java >= 7 installed in your system.

To enable the Docker sandbox (recommended for grading untrusted
student submissions), you also need Docker installed and reachable on
your PATH. See [Docker sandbox](#docker-sandbox) below.

## Usage

The top level directory contains the framework scripts (test runner,
aggregator, and templator). The pam directory contains the Python
AutoMarker with instructions and examples, and the jam directory
contains the Java AutoMarker with instructions and examples.

See README files for [pam](./pam/README.md) and [jam](./jam/README.md)
for specific instructions.

A high-level map of the codebase, written for new contributors and AI
assistants, lives in [AGENTS.md](./AGENTS.md).

## Docker sandbox

Student code is untrusted: an assignment might infinite-loop, write
gigabytes to disk, or attempt to phone home. The test runner can wrap
every `test_cmd` in a disposable Docker container so that student code
runs in isolation, with bounded CPU, memory, disk, and wall-clock
limits, and (by default) no network access.

### Enabling

Set `docker_enabled = True` in your `config.py`. All other Docker
options are optional; defaults come from
[utils/defaults.py](./utils/defaults.py).

```python
# Minimal config: enable Docker with all defaults.
docker_enabled = True
```

### Full set of options

```python
docker_enabled = True
docker_image = 'python:3.11-slim'   # image used to run student code
docker_cpus = '1.0'                 # fractional CPU cores (Docker --cpus)
docker_memory = '256m'              # memory cap (Docker suffixes: k/m/g)
docker_disk = '1g'                  # container rootfs cap (--storage-opt size)
docker_timeout = 60                 # per-command wall-clock limit, seconds
docker_network = 'none'             # 'none' isolates from network; 'bridge' restores it
docker_drop_capabilities = True     # drop ALL Linux caps + no-new-privileges
docker_workdir = '/submission'      # mount point inside the container
docker_binary = 'docker'            # override if docker is not on PATH
```

| Setting | Maps to | Notes |
| --- | --- | --- |
| `docker_image` | image tag | Pick one that already has your test toolchain (Python for pam, JDK for jam). |
| `docker_cpus` | `--cpus` | Fractional cores. `'0.5'` is half a core. |
| `docker_memory` | `--memory` / `--memory-swap` | Swap is disabled by setting both equal. |
| `docker_disk` | `--storage-opt size=` | Requires a Docker storage driver that supports per-container quotas (overlay2 on xfs+pquota, devicemapper, btrfs, zfs). Docker rejects the option on other drivers — leave `docker_disk` unset there, or switch storage driver. |
| `docker_timeout` | `timeout --signal=KILL` inside the container | Enforced in two places: as a `subprocess` timeout on the host, and via `timeout(1)` inside the container, so a student process that ignores signals still dies. Make sure `config.timeout` is `>=` `docker_timeout`. |
| `docker_network` | `--network` | `'none'` blocks all networking (default). Use `'bridge'` only if tests legitimately need it. |
| `docker_drop_capabilities` | `--cap-drop ALL --security-opt no-new-privileges` | Strongly recommended. |

### How it works

When Docker is enabled:

1. `test_runner.py` checks that the Docker binary is on PATH and fails
   fast with a clear message if not.
2. `preamble_cmd` and `postamble_cmd` continue to run **on the host**
   (they normally copy test files into the student directory and
   clean them up).
3. Each entry in `test_cmd` is wrapped with `docker run --rm` and
   executed as `sh -c '<your command>'` inside the container, with the
   student's directory bind-mounted at `docker_workdir` (default
   `/submission`).
4. The container is removed automatically (`--rm`) when the command
   exits, regardless of success or failure.

### Notes and limitations

- Paths inside `test_cmd` must make sense **inside the container**.
  If your command references absolute host paths (e.g. `path_to_uam`
  in [pam/examples/config.py](./pam/examples/config.py)), make sure
  those paths exist inside the chosen image, or build a custom image
  that bundles them, or use `preamble_cmd` to stage the files into
  the student directory (which *is* mounted) before tests run.
- `--storage-opt size=` is the only knob Docker offers for capping a
  container's rootfs size, and it depends on the storage driver. If
  your driver does not support it, omit `docker_disk` and rely on
  memory + timeout limits instead.
- On Linux, the bind mount lets students write back into their
  submission directory — this is intentional so `result.json` ends up
  in the right place for the aggregator.

## Support

Please send comments, feedback and bugs to
[anya@cs.utoronto.ca](mailto:anya@cs.utoronto.ca). Currently, there is
very limited support provided. We hope to improve.
