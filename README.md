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
docker_user = 'host'                # 'host' = current UID:GID; '' to disable
docker_workdir = '/submission'      # mount point inside the container
docker_binary = 'docker'            # override if docker is not on PATH
```

| Setting | Maps to | Notes |
| --- | --- | --- |
| `docker_image` | image tag | Pick one that already has your test toolchain (Python for pam, JDK for jam). |
| `docker_cpus` | `--cpus` | Fractional cores. `'0.5'` is half a core. |
| `docker_memory` | `--memory` / `--memory-swap` | Swap is disabled by setting both equal. |
| `docker_disk` | `--storage-opt size=` **and** `--ulimit fsize=` | Two-pronged cap. The storage-opt half limits the container's writable rootfs but only works on storage drivers that support per-container quotas (overlay2 on xfs+pquota, devicemapper, btrfs, zfs); other drivers — including the very common overlay2-on-ext4 and the newer `overlayfs` rootless driver — silently ignore it. The ulimit half caps the maximum size of any *single* file the process can create and is enforced by the kernel via `RLIMIT_FSIZE`, so it works everywhere. Together they catch single-file disk-fill attacks even when the storage driver doesn't help. See [Bind mounts and disk usage](#bind-mounts-and-disk-usage). |
| `docker_timeout` | `timeout --signal=KILL` inside the container | Enforced in two places: as a `subprocess` timeout on the host, and via `timeout(1)` inside the container, so a student process that ignores signals still dies. Make sure `config.timeout` is `>=` `docker_timeout`. |
| `docker_network` | `--network` | `'none'` blocks all networking (default). Use `'bridge'` only if tests legitimately need it. |
| `docker_drop_capabilities` | `--cap-drop ALL --security-opt no-new-privileges` | Strongly recommended. Combined with `docker_user`, this means the container runs as a normal, unprivileged user. |
| `docker_user` | `--user` | Defaults to the sentinel `'host'`, which resolves at runtime to `f"{euid}:{egid}"` of the user running `test_runner.py`. This is required when `docker_drop_capabilities = True`: dropping `CAP_DAC_OVERRIDE` means container-root can no longer write to a bind mount it does not own. Set to an explicit `'1000:1000'` / `'root'` to override, or to `''`/`None` to use whatever USER the image declares. |

### End-to-end examples

Two ready-to-run examples exercise every Docker knob against a curated
mix of correct, buggy, and actively malicious submissions:

- [pam/docker_examples](./pam/docker_examples/) — Python, uses
  `python:3.11-slim`.
- [jam/docker_examples](./jam/docker_examples/) — Java, uses
  `openjdk:11-slim`.

Each example has its own README documenting which sandbox setting
each submission is intended to exercise.

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
- On Linux, the bind mount lets students write back into their
  submission directory — this is intentional so `result.json` ends up
  in the right place for the aggregator.

### Bind mounts and disk usage

`docker_disk` is enforced in two ways at the same time:

1. **`--storage-opt size=<spec>`** caps the container's writable
   rootfs layer. Only some storage drivers honour this option: overlay2
   on XFS+pquota, devicemapper, btrfs, zfs. The default on most Linux
   hosts — overlay2 on ext4, and the newer rootless `overlayfs` driver
   — silently ignores it. To check whether your installation enforces
   it:

   ```sh
   docker info | grep 'Storage Driver'
   docker run --rm --storage-opt size=1g python:3.11-slim \
       sh -c 'dd if=/dev/zero of=/tmp/x bs=1M count=1500 2>&1 | tail -1'
   ```

   If the `dd` writes the full 1.5 GiB, the option is being ignored.

2. **`--ulimit fsize=<bytes>`** caps the maximum size of any *single*
   file the process can create. This is enforced unconditionally by
   the kernel via `RLIMIT_FSIZE` and works on every storage driver.
   It catches a student writing one huge file (the most common
   disk-fill pattern), but does not bound the *total* of many small
   files.

What `docker_disk` cannot do on its own:

- Cap writes to the bind-mounted submission directory. The bind mount
  passes straight through to the host filesystem; the storage-opt half
  doesn't see it at all, and the ulimit half only caps individual
  files inside it.
- Stop a student writing thousands of small files on a storage driver
  that ignores `--storage-opt`. The ulimit cap is per-file.

For comprehensive disk safety in production, layer a filesystem quota
on the host directory that holds student submissions. On Linux, the
canonical mechanisms are XFS project quotas (`xfs_quota -x`) or ext4
quotas (`quotaon`, `setquota`). With one of those in place,
`docker_disk` becomes the inner ring of defence and the host quota the
outer.

The bundled [diskhog example](./pam/docker_examples/submissions/diskhog/A1/solution.py)
writes one large file to `/tmp/diskhog.bin`, so the ulimit half of
`docker_disk` catches it on every storage driver.

### Container UID and bind-mount permissions

`docker_user` (default `'host'`) is what makes the sandbox usable
together with `docker_drop_capabilities = True`. Without it, container
processes run as root, but `--cap-drop ALL` strips
`CAP_DAC_OVERRIDE` — the capability that lets root bypass file
permissions. The result is that container-root can no longer write to
a bind mount it does not own, which manifests as `PermissionError`
when your test command tries to drop `result.json` into the student
directory. Running as the host UID:GID sidesteps the problem and as a
bonus means the container is never root in the first place.

If you keep `docker_drop_capabilities = False`, you can also keep
`docker_user = ''` / `None` and let container-root use
`CAP_DAC_OVERRIDE` instead — but you trade away most of the sandbox.

## Support

Please send comments, feedback and bugs to
[anya@cs.utoronto.ca](mailto:anya@cs.utoronto.ca). Currently, there is
very limited support provided. We hope to improve.
