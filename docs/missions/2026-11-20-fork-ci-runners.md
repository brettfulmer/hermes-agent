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

## Follow-up: measured first-run failures

Published head `a7903ad79f3ff5bd8c108724fd9a60ca33a22cfe` ran on standard
GitHub runners. Docker `44540373223` and Nix `44540373133` passed. CI
`44540373371` failed its real aggregate gate. The obsolete prior run's queued
Blacksmith aggregate required a specifically authorised force-cancel after normal
cancellation failed; current-head gates were preserved.

Root extended the repair scope to contributor attribution, the missing Codex
credential-source documentation, Windows Git lookup, and suspended-process test
synchronisation. Prepared fixes retain all test selectors and safety assertions.
GitHub annotations confirm the three Python slices and JS job exceeded their
30-minute limits; the slowest Python slice reached 74%. Fork-only 60-minute job
budgets and serial JS workspace scheduling address the measured smaller-runner
capacity. Per-test deadlines are unchanged. macOS ARM jobs could not acquire a
runner; GitHub explicitly reported hosted ARM capacity constraints.

Native focused evidence: docs drift 2 passed; containment 8 passed; managed lookup
guard 8 passed; Git unit/live suites 11 passed with one platform skip. The two
new Git invariants fail on detached baseline `eaac327fac2c` and pass on the patch.
Contributor mapping passes its canonical guard. The Linux compression/restart FIFO
journey reproduces both failures on baseline `eaac327fac2c`, at the same
`FOLLOWER_1` transcript assertion as current CI. Root-cause investigation remains
open; no gateway behaviour was changed. Independent review returned SHIP. The
17-check run passed 15 checks but two exhausted host memory; both failed checks
passed on isolated canonical reruns. Publication and new remote checks remain pending.

## Approved test-boundary correction

Root approved a test-only correction after the Linux journey probe showed that
`PRESSURE_1` already belonged to the committed protected tail before restart.
The replacement must compare each follower's wire history with the actual
pre-restart committed prefix, prohibit resurrection of the nonempty set of
actually summarised parent rows, and prove that deliberately reinjecting one
such row fails. FIFO, exactly-once, admission identity, lineage, and single-summary
assertions remain unchanged. Compression policy and gateway runtime are out of scope.

The corrected test passes both graceful/crash cases on native Linux in the isolated
WSL test environment (19.6 seconds). Each case also verifies that appending a real
summarised parent row to an otherwise valid follower history raises the resurrection
assertion. Synthetic pressure input has no incidental trailing space, making its
stored and wire text byte-identical under the gateway's existing input trim.
The old assertion failed on both baseline and published head because `PRESSURE_1`
was already in the committed protected tail, not resurrected by restart.
Independent read-only review returned SHIP and reproduced both passing Linux cases;
all 17 staged checks passed together with zero code-health findings.
