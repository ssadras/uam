## PAM Docker sandbox example

This example exercises the Docker sandbox end-to-end against a curated
set of "students" whose submissions range from a clean reference
solution to actively malicious code. It is the recommended way to
validate that the sandbox is configured correctly on your grading
host.

> **Warning.** Several submissions try to spin forever, exhaust
> memory, fill the disk, fork excessively, dial out over the network,
> and read sensitive host paths. **Run this only with Docker enabled**
> (the bundled [config.py](./config.py) sets `docker_enabled = True`).
> Outside the sandbox these submissions can damage your host.

### Layout

```
pam/docker_examples/
├── config.py            # Docker-enabled UAM config
├── directories.txt      # one submission path per line
├── dirs_and_names.txt   # submission path,name pairs
├── groups.txt           # group-name,dir-name,student-id
├── students.csv         # classlist
├── test_solution.py     # self-contained UAM test driver (no extra deps)
└── submissions/
    ├── correct/A1/solution.py        # passes everything
    ├── failures/A1/solution.py       # wrong answers
    ├── errors/A1/solution.py         # raises uncaught exceptions
    ├── infloop/A1/solution.py        # spins forever  -> docker_timeout
    ├── forkbomb/A1/solution.py       # fork() in a loop -> PID/CPU caps
    ├── memhog/A1/solution.py         # allocates ~1 GiB -> docker_memory
    ├── diskhog/A1/solution.py        # writes ~2 GiB    -> docker_disk
    ├── network/A1/solution.py        # outbound socket  -> docker_network=none
    └── host_escape/A1/solution.py    # probes /etc/shadow, /proc, /tmp
```

The bundled [test_solution.py](./test_solution.py) is a deliberately
simple, stdlib-only UAM test driver. It runs a fixed spec against the
student's `solution.py` and writes a UAM-compatible `result.json`.
Using it instead of [pam.py](../pam.py) keeps the example reproducible
with a vanilla `python:3.11-slim` image (no `testtools` install
needed inside the sandbox).

### Run

1. Install Docker and pull the base image:

   ```sh
   docker pull python:3.11-slim
   ```

2. From the repository root, run the test runner:

   ```sh
   python3 test_runner.py pam/docker_examples/config.py
   ```

3. After the run, each `submissions/*/A1` directory should contain a
   `result.json`. Aggregation and templating work exactly like in the
   standard example:

   ```sh
   python3 aggregator.py A1 \
       pam/docker_examples/dirs_and_names.txt \
       pam/docker_examples/students.csv \
       pam/docker_examples/groups.txt
   python3 templator.py aggregated.json html
   ```

### What each submission proves

| Submission | Sandbox knob it exercises | Expected outcome |
| --- | --- | --- |
| `correct` | baseline | all spec tests recorded as passes |
| `failures` | baseline | wrong answers recorded under `failures` |
| `errors` | baseline | exceptions recorded under `errors` |
| `infloop` | `docker_timeout` + `timeout(1)` inside the container | container killed at ~30 s; host stays responsive |
| `forkbomb` | dropped capabilities, container PID namespace | bomb confined to the container; host process table untouched |
| `memhog` | `docker_memory` / `--memory-swap` (swap disabled) | OOM-killed by Docker before host memory is touched |
| `diskhog` | `docker_disk` (`--storage-opt size=`) | writes to `/tmp/diskhog.bin` (container rootfs); fails with ENOSPC at the `docker_disk` cap. Note: writes to the bind-mounted `/submission` would *not* be caught by this knob — see the top-level README's [Bind mounts and disk usage](../../README.md#bind-mounts-and-disk-usage). |
| `network` | `docker_network = 'none'` | socket calls fail with EHOSTUNREACH / EAI_AGAIN |
| `host_escape` | bind-mount scope, dropped caps, `no-new-privileges` | reads return image-only data, not host files; writes outside `/submission` evaporate with `--rm` |

If any row above produces a different outcome, the sandbox is
mis-configured — check your Docker storage driver (for `docker_disk`)
and `--cap-drop`/`--security-opt` support, and consult the
[Docker sandbox section](../../README.md#docker-sandbox) of the
top-level README.
