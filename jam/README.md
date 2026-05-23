## JAM — Java AutoMarker

JAM grades JUnit 4-based Java assignments. The JAM test runner is a
JUnit `RunListener` that captures per-test results and exception traces
and emits a UAM-compatible JSON.

This README walks through the three stages of the pipeline:
**Compile**, **Grade**, **Aggregate**, **Format**. For a high-level
overview of the framework itself, see the top-level
[README](../README.md). For sandboxing student code with Docker, see
[Docker sandbox](#docker-sandbox) below.


## Compile JAM

 Make sure [compile_jam.sh](./compile_jam.sh) is executable. Then:

`./compile_jam.sh`

 You only need to do this once.


## Grade

1. Student submissions.

You need a file that lists all directories containing student
submissions.  The directory [examples](./examples) contains six
"student" submissions, from students *correct*, *failures*, *infloop*,
*nosubmissions*, *nullpointer*, and *syntax* (see directory
[examples/submissions](./examples/submissions)). Each submission is in
a folder named A1.  Therefore, you need the file (see
[directories.txt](./examples/directories.txt)) with the following
contents:

`jam/examples/submissions/correct/A1`  
`jam/examples/submissions/failures/A1`  
`jam/examples/submissions/infloop/A1`  
`jam/examples/submissions/nosubmission/A1`  
`jam/examples/submissions/nullpointer/A1`  
`jam/examples/submissions/syntax/A1`  


Note that all paths are relative to the location of
[test_runner.py](../test_runner.py).


2. Test file(s).

You need your JAM test files for testing each individual submission.
You also may need additional files to run your tests (for example,
starter files you distributed to students and instructed them to not
modify them).

**Requirements** for the test files:

Starting with your "normal" JUnit4 test file, you create a JAM test
file as follows:

`import edu.toronto.cs.jam.annotations.Description;`

For each @Test method, use the following annotations:

`@Test(timeout=XXX)`  
`@Description(description="description of your test method")`  


The directory [examples/tests](./examples/tests) contains a sample
test suit for A1.

3. Configure test_runner.py.

You need a configuration file. See
[examples/config.py](./examples/config.py). At a minimum, update
`uam_dir` to the absolute path of your UAM checkout.

4. Finally,

`python3 test_runner.py path/to/configfile`

If everything went well, you should have a .json file in each student
submission directory.

## Aggregate


1. Student information.

You need a classlist (see [students.csv](./examples/students.csv)) in
the following format:

`student-id,first-name,last-name,student-number,email`

TIP: if you are at UofT, you can get this list from
Quercus/Intranet/your-dept-sysadmin.

2. Group information.

If your students were working in groups and submitted one solution per
group, then you need a file that records this information. It should
be in the format (see [groups.txt](./examples/groups.txt)):

`group-name,dir-name,student-id-1,student-id-2,...`

Actually, even if your students were working individually, you still
need this file. In other words, we assume that students *always* work
in groups. When they work individually, the group size is 1, and you
have a group per student.

TIP: If you are using MarkUs, you can download this file from your
MarkUs web interface.

3. Name matching.

You need a file that matches submission directories with group
names. See [dirs_and_names.txt](./examples/dirs_and_names.txt) for an
example.

4. Finally,

`python3 aggregator.py A1 jam/examples/dirs_and_names.txt jam/examples/students.csv jam/examples/groups.txt`

See
  `python3 aggregator.py --help`
for more options and full documentation.

If all went well, you should have a file `aggregated.json` that contains
full results of running all tests on all student submissions.


##  Format

JSONs are great, but we want good looking summaries.

1. In the configuration file, specify where your templates are. See
sample [config.py](./examples/config.py).

The templates we currently provide are: HTML (aggregate), txt (both
individual and aggregate), markus that contains a csv grades table
(aggregate), and a .gf file (aggregate). We are working on many more.

You are welcome to contribute your own templates!

2. Some examples:

`python3 templator.py aggregated.json html`  
`python3 templator.py aggregated.json txt`  
`python3 templator.py aggregated.json markus`  

See 
  `python3 templator.py --help`
for full information and more options.


## Docker sandbox

When `docker_enabled = True` is set in your config, each `test_cmd`
runs inside a disposable Docker container with CPU, memory, disk, and
wall-clock limits applied. The student's submission directory is
bind-mounted into the container so `result.json` still ends up in the
expected place for the aggregator.

The bundled example config [examples/config.py](./examples/config.py)
includes a commented-out Docker block you can adapt. For the full
explanation of each setting, see the
[Docker sandbox section](../README.md#docker-sandbox) of the top-level
README.

A complete, end-to-end Docker example — with a self-contained Java
test driver (no JUnit/JAM jars needed inside the sandbox) and
submissions covering correct, buggy, and actively malicious code
(infinite loop, memory hog, network calls, host-filesystem probes) —
lives in [docker_examples/](./docker_examples/). Use it to validate
your sandbox setup.

Jam-specific tips:

- Use an image with a matching JDK — `openjdk:11-slim` works for most
  introductory courses.
- Jam's `test_cmd` relies on classpaths that point at JAM libs and the
  exception-explanations XML. Those paths must resolve **inside the
  container**. Either:
  - copy the JAM jars and tests into the student directory in
    `preamble_cmd` (which runs on the host) and reference them with
    paths relative to `docker_workdir`, or
  - build a custom image that bundles UAM and the JAM jars at known
    paths, and point `docker_image` at it.
- Java compilation and JVM start-up are significantly more expensive
  than Python — bump `docker_memory` (e.g. `'512m'` or `'1g'`) and
  `docker_timeout` accordingly.


## Support

Please send comments, feedback and bugs to
[anya@cs.utoronto.ca](mailto:anya@cs.utoronto.ca). Currently, there is
very limited support provided. We hope to improve.
