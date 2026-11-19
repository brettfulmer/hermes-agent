# Mission: Run public-fork CI on standard GitHub runners

**Started:** 2026-11-20
**Requested by:** Brett Fulmer
**Status:** IN PROGRESS

## What was asked
Restore ordinary PR validation in `brettfulmer/hermes-agent`, where upstream
Blacksmith runner labels leave jobs queued without an assigned runner.

## Goal and scope
Use standard GitHub-hosted runners only in this public fork, preserving upstream
runner choices, architecture coverage, test discovery and the aggregate gate.
Bound fork test concurrency to its runner capacity. Document the fallback.

## Out of scope
Release-only and publishing jobs, signed installers, disabled desktop workflows,
repository settings, provider changes, paid services and fixture cleanup.

## Definition of done
- The ordinary PR call graph selects supported standard runners in this fork.
- Existing CI routing and job-graph tests and the blocking checker pass locally.
- Independent review precedes commit and push; GitHub CI confirms execution after
  publication. Root session owns publication and final remote verification.

## Assumptions made
This public fork can use free standard runners. Docker build/publish guards remain
upstream-only. Existing timeouts stay unchanged until measured evidence warrants it.

## Outcome: 2026-11-20
**Status:** PARTIAL

Runner compatibility is implemented and independently reviewed. Semantic YAML
comparison confirmed all 26 changed values are runner/worker settings, preserving
upstream values and all remaining workflow behaviour. `just check --staged`
passed all 17 checks with zero code-health findings. Job-graph tests passed 2/2;
routing tests passed 105 with one host-specific skip (282 seconds).

The first combined test attempt exceeded the local 300-second file cap during
concurrent checker execution; its buffered output showed two failures without
tracebacks. An isolated canonical rerun with `--file-timeout 600 -x` passed.
No hosted timeout or test selector changed. The unrestricted working-tree checker
failed only on the preserved untracked fixture binary; candidate-artifact checks
passed without changing or including that fixture.

Remote CI runner assignment and final CI results remain pending publication.
