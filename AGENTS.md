# AGENTS.md

Guidance for AI agents working in this repository.

## Project: UAM (Universal AutoMarker)

UAM is a framework for batch-grading student programming assignments. It runs
language-specific test harnesses against student submissions, aggregates the
JSON results, and renders human-readable reports from Jinja2 templates.

Currently shipped language support:

- **pam** — Python AutoMarker (mature, wraps `unittest`)
- **jam** — Java AutoMarker (mature, wraps JUnit 4 via a custom `JAMCore` runner)

Planned: SQL (sqam), Racket (ram), Haskell (ham).

## Pipeline

The framework is a three-stage pipeline; each stage is a standalone script
driven by a user-supplied Python config module.

```
            ┌──────────────────┐    ┌────────────────┐    ┌────────────────┐
submissions │  test_runner.py  │ -> │  aggregator.py │ -> │  templator.py  │ -> reports
            └──────────────────┘    └────────────────┘    └────────────────┘
            per-student JSON       single aggregated JSON   HTML / TXT / GF / MarkUs CSV
```

1. **`test_runner.py`** — for each student directory, runs `preamble_cmd`,
   then each command in `test_cmd`, then `postamble_cmd`. Each command runs
   with a per-process timeout. Students are processed in parallel via
   `multiprocessing.Pool`. Produces `result.json` in every submission
   directory.
2. **`aggregator.py`** — reads each per-student JSON, joins it with student
   and group metadata (classlist + groups file), and writes a combined
   `aggregated.json`.
3. **`templator.py`** — renders the aggregated JSON (and/or each individual
   JSON) through Jinja2 templates under [templates/](templates/).

There is also **`grade.py`**, a thin wrapper around `test_runner.py` for
re-grading individual submissions by repo name.

## Key files

| Path | Purpose |
| --- | --- |
| [test_runner.py](test_runner.py) | Orchestrates test execution per student. |
| [grade.py](grade.py) | Re-run tests on selected submissions. |
| [aggregator.py](aggregator.py) | Combines per-student JSON into `aggregated.json`. |
| [templator.py](templator.py) | Renders reports from JSON via Jinja2. |
| [pam/pam.py](pam/pam.py) | Python test harness — runs `unittest.TestCase`s with per-test timeout, emits UAM JSON. |
| [jam/](jam/) | Java test harness — JUnit4 with custom annotations, compiled via [jam/compile_jam.sh](jam/compile_jam.sh). |
| [utils/defaults.py](utils/defaults.py) | Framework-wide defaults (timeout, template names, JSON filenames). |
| [utils/uam_utils.py](utils/uam_utils.py) | `Student` / `Group` models used by the aggregator. |
| [utils/plugins.py](utils/plugins.py) | Jinja2 filter functions exposed in templates. |
| [utils/utils.py](utils/utils.py) | Auxiliary tooling for classlist / Quercus / gf grade files. |
| [templates/](templates/) | Jinja2 templates organised by output type (`html`, `txt`, `gf`, `markus`). |

## Config files

Every run is driven by a Python module the user supplies as a CLI argument.
See [pam/examples/config.py](pam/examples/config.py) and
[jam/examples/config.py](jam/examples/config.py) for canonical examples.

Expected attributes (all are referenced via `config.<name>`):

- `students_fname` — path to a file listing submission directories, one per line.
- `max_processes` — pool size for parallel grading.
- `timeout` — per-`test_cmd` timeout in seconds.
- `timeout_operation` — callable invoked when a `test_cmd` times out (typically writes a marker file).
- `preamble_cmd`, `test_cmd` (list), `postamble_cmd` — shell commands run inside each student directory.
- `template_dir` — path to the Jinja2 template root.
- Docker-related attributes (optional) — see [Docker sandboxing](#docker-sandboxing).

## Docker sandboxing

`test_runner.py` can execute each `test_cmd` inside a Docker container so that
malicious or buggy student code is isolated from the host. The image and
resource limits are configurable; see [utils/defaults.py](utils/defaults.py)
for the default image and limits, and [utils/docker_runner.py](utils/docker_runner.py)
for the command-building logic.

When `docker_enabled = True` in the config, `test_runner.py` wraps each entry
of `config.test_cmd` with `docker run`, bind-mounts the student directory
read-write into the container, and applies the configured CPU, memory, disk,
and time limits. Preamble and postamble commands always run on the host
(they typically copy test files in and clean them out afterward).

End-to-end smoke tests for the sandbox live in
[pam/docker_examples](pam/docker_examples/) and
[jam/docker_examples](jam/docker_examples/). Each has submissions covering
correct, buggy, and actively malicious code; their READMEs map every
submission to the specific `docker_*` setting it exercises. Treat these as
the regression suite when changing anything in `utils/docker_runner.py` or
`test_runner.py`.

## Conventions and gotchas

- **Platform.** `test_runner.py` uses `os.killpg` and `start_new_session=True`,
  so it targets POSIX. Windows users should run via WSL or rely on the Docker
  sandbox. `pam.py` uses `signal.SIGALRM`, which is also POSIX-only.
- **Working directory.** `test_runner.execute_tests` calls `os.chdir(student)`
  and never restores the cwd — relying on `multiprocessing` to give each
  worker its own process. Do not call this function from the same process
  twice in a row expecting the cwd to be preserved.
- **Shell commands.** `test_cmd`, `preamble_cmd`, `postamble_cmd` are executed
  with `shell=True`. They are sourced from a trusted config module, not from
  student input, but be careful when interpolating paths.
- **Python version.** Requires Python ≥ 3.3. The `Timeout` mechanism in
  `pam.py` uses `signal.alarm`, which only works on the main thread.
- **JSON contract.** The shape of `result.json` (per-student) and
  `aggregated.json` is the implicit contract between all three pipeline
  stages and the templates. Treat the keys (`results`, `tests`, `students`,
  `date`, `assignment`, `origin`) as load-bearing — changing them will break
  templates in [templates/](templates/).
- **Imports of config.** Both `test_runner.py` and `aggregator.py` resolve
  the config file by appending its directory to `sys.path` and
  `importlib.import_module`-ing it. The config file's basename therefore
  becomes a module name and must be a valid Python identifier.

## How to verify changes

There is no automated test suite for the framework itself. To smoke-test:

1. From the repo root, run pam against the bundled examples:
   ```
   python3 test_runner.py pam/examples/config.py
   ```
   (Edit `path_to_uam` in [pam/examples/config.py](pam/examples/config.py)
   first.) Confirm a `result.json` appears under each submission directory.
2. Run aggregation:
   ```
   python3 aggregator.py A1 pam/examples/dirs_and_names.txt \
       pam/examples/students.csv pam/examples/groups.txt
   ```
3. Render reports:
   ```
   python3 templator.py aggregated.json html
   ```

For jam, run [jam/compile_jam.sh](jam/compile_jam.sh) once, then follow the
same three steps with [jam/examples/config.py](jam/examples/config.py).

## Style

- Match the existing module-docstring header style (author + year) when
  adding new top-level modules.
- Keep new defaults in [utils/defaults.py](utils/defaults.py) rather than
  scattering literals through the code.
- Avoid breaking the existing config attribute names — they are part of the
  public surface that every user's `config.py` depends on.
