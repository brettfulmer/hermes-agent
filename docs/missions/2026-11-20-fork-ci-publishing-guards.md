# Mission: restore fork CI without inherited publishing

**Status:** IN PROGRESS
**Requested by:** Brett Fulmer, through the root delivery session.

GitHub paused Actions on `brettfulmer/hermes-agent` because of fork usage scale.
Its official restoration control applies to the repository, so default-main
publishing schedules must be guarded before using it. This isolated branch starts
at fork main `eaac327fac2c`, separate from runtime PR1 (`4ae5694f5e`).

## Scope and acceptance

- Exclude this fork from inherited canary publishing/pruning, artifact archival,
  JS auto-fix writes, Vercel deployment, skills-index deployment and standalone OSV.
- Preserve every original condition for upstream and other repositories, all
  ordinary PR lanes, runners, triggers, permissions, secrets and services.
- Independently review the precise guards and run canonical/static checks before
  commit and the authorised guard-only bootstrap merge. Runtime PR1 still requires
  real current-head checks before its separate merge.
- Guard-only configuration must reach default main before repository-wide Actions
  restoration. Candidate-only guards cannot protect default-branch schedules.

## Current controls

Live GitHub checks returned no main branch protection (404), no applicable branch
rules and no repository rulesets. AGENTS requires canonical tests/local checks and
main ancestry; CONTRIBUTING requires those before submission. No explicit remote-
CI-only bootstrap approval rule was found. Root explicitly authorised the reviewed
guard-only configuration repair through the normal PR path while online CI is
unavailable. No protected rule, permission, runner, service or billing change is allowed.

## Local verification and independent review

Eight job conditions across six workflow files exclude only this fork. The static
verifier passed 10,752 job/context evaluations, preserving upstream and other-fork
semantics, including cancelled/skipped dependencies and implicit status checks.
All non-conditional fields and ordinary PR workflow files are unchanged. The
already-reviewed public author mapping is reused for this branch's CI attribution.

All 17 staged checks passed; workflow graph tests passed 2/2. The canonical routing
suite passed 104 with one host skip and one Windows Bash startup timeout. Its full
32-case affected matrix passed on isolated canonical retry without source changes.
Independent read-only review returned SHIP and repeated the semantic verification.
Online CI is unavailable for this bootstrap due to GitHub's fork-scale pause;
there is no claim of an online passing bootstrap gate. The separate runtime PR
must still pass every real current-head required check after restoration.
