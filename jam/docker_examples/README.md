## JAM Docker sandbox example

This example exercises the Docker sandbox end-to-end against a curated
set of "students" whose submissions range from a clean reference
solution to actively malicious code. It is the recommended way to
validate that the sandbox is configured correctly on your grading
host.

> **Warning.** Several submissions try to spin forever, exhaust
> memory, dial out over the network, and read sensitive host paths.
> **Run this only with Docker enabled** (the bundled
> [config.py](./config.py) sets `docker_enabled = True`). Outside the
> sandbox these submissions can damage your host.

### Layout

```
jam/docker_examples/
├── config.py                 # Docker-enabled UAM config
├── directories.txt           # one submission path per line
├── dirs_and_names.txt        # submission path,name pairs
├── groups.txt                # group-name,dir-name,student-id
├── students.csv              # classlist
├── tests/
│   └── TestSolution.java     # self-contained UAM test driver (no JUnit)
└── submissions/
    ├── correct/A1/a1soln/Solution.java       # passes everything
    ├── failures/A1/a1soln/Solution.java      # wrong answers
    ├── infloop/A1/a1soln/Solution.java       # spins forever  -> docker_timeout
    ├── memhog/A1/a1soln/Solution.java        # allocates ~1 GiB -> docker_memory
    ├── network/A1/a1soln/Solution.java       # outbound socket  -> docker_network=none
    └── host_escape/A1/a1soln/Solution.java   # probes /etc/shadow, /proc, /tmp
```

The bundled [TestSolution.java](./tests/TestSolution.java) is a
deliberately simple, JDK-only UAM test driver. It runs a fixed spec
against the student's `a1soln.Solution` class and writes a
UAM-compatible `result.json`. Using it instead of the standard JAM
runner keeps the example reproducible with a vanilla
`openjdk:11-slim` image (no JUnit/JAM jars needed inside the sandbox).

### Run

1. Install Docker and pull the base image:

   ```sh
   docker pull openjdk:11-slim
   ```

2. From the repository root, run the test runner:

   ```sh
   python3 test_runner.py jam/docker_examples/config.py
   ```

3. After the run, each `submissions/*/A1` directory should contain a
   `result.json`. Aggregation and templating work exactly like in the
   standard example:

   ```sh
   python3 aggregator.py A1 \
       jam/docker_examples/dirs_and_names.txt \
       jam/docker_examples/students.csv \
       jam/docker_examples/groups.txt
   python3 templator.py aggregated.json html
   ```

### What each submission proves

| Submission | Sandbox knob it exercises | Expected outcome |
| --- | --- | --- |
| `correct` | baseline | all spec tests recorded as passes |
| `failures` | baseline | wrong answers recorded under `failures` |
| `infloop` | `docker_timeout` + `timeout(1)` inside the container | container killed at ~60 s; host stays responsive |
| `memhog` | `docker_memory` / `--memory-swap` (swap disabled) | JVM `OutOfMemoryError` or OOM-kill *inside* the container |
| `network` | `docker_network = 'none'` | `Socket.connect` fails with `NoRouteToHostException` / `UnknownHostException` |
| `host_escape` | bind-mount scope, dropped caps, `no-new-privileges` | reads return image-only data, not host files; writes outside `/submission` evaporate with `--rm` |

If any row above produces a different outcome, the sandbox is
mis-configured — check your Docker storage driver (for `docker_disk`)
and `--cap-drop`/`--security-opt` support, and consult the
[Docker sandbox section](../../README.md#docker-sandbox) of the
top-level README.
