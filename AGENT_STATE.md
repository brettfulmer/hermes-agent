# Active bounded integration

Current restoration checkpoint: guard-only PR2 merged as `7c5c71bca9` on fork main,
with independent SHIP and local canonical/static checks while online CI was paused.
Main's complete tree matches the reviewed guard artifact `9e5c88852a`. This merge
integrates those eight publishing/write exclusions into the runtime branch; all
Python code/tests and ordinary PR workflow files remain identical to `4ae5694f5e`.
The official Actions restoration control and real final-head macOS/aggregate checks
remain required. Runtime PR1 must not merge before those real checks pass.

Earlier CI checkpoint: public PR head `9e5d0c5306` passed every long Linux, Windows,
and JS lane; macOS slice 1 exposed the budget-expired BEGIN error classification
and the aggregate correctly failed. The current focused repair moves BEGIN inside
the existing transaction guard. The new expired-case regression was proven red;
the ordinary-error case preserves the original exception. After the fix, native
Windows schema-browse tests pass 20 with 11 host skips, and Linux passes all 31.
No installed runtime or live database was changed. Independent review returned SHIP,
and all 17 staged checks passed together. Exact-commit checks and a new real
macOS/aggregate verdict are required before merge.

Active CI repair: [Public-fork CI runners](docs/missions/2026-11-20-fork-ci-runners.md).
Work is isolated to ordinary PR workflow runner compatibility; independent review
cleared the candidate. All 17 staged blocking checks pass, job-graph tests pass 2/2,
and the isolated routing rerun passes 105 tests with one host-specific skip.
The first combined routing attempt exceeded the local file cap during concurrent
checker execution; no hosted timeout or selectors changed. Commit-artifact checks,
publication and remote runner assignment remain pending. Both untracked fixture
directories remain untouched and excluded from the candidate.

CI follow-up checkpoint: published head `a7903ad79f` has Docker/Nix success but
CI `44540373371` failed. Current uncommitted repair owns fork job capacity,
contributor attribution, Codex config documentation, PM/PATH/ucrt64 Git lookup,
and suspended-process test synchronisation. Native focused tests pass; two new
Git invariants were proven red on detached baseline `eaac327fac2c`. Linux FIFO
also reproduces both failures on that baseline, at the same transcript assertion
as current CI; root-cause investigation is open without gateway behaviour changes.
Independent review returned SHIP. All 17 checks have passed across the initial
15 successful checks and isolated retries of two host-memory failures. New remote
checks are still required after publication.

FIFO test-only checkpoint: the old `PRESSURE_1`-must-disappear assertion contradicts
the actual committed protected tail. The replacement compares the exact committed
prefix on each follower and rejects actually summarised parent rows; its deliberate
reinjection negative control must fail. Both graceful/crash journeys now pass on
native Linux. Production compression/gateway code is unchanged. Independent read-only
review returned SHIP and independently passed both Linux cases; all 17 staged checks
passed together. Exact-commit and new remote checks are required before merge.

Mission: [Codex CLI access source](docs/missions/2026-11-19-codex-cli-access-source.md).

The opt-in access-only source preserves the native tool loop. Auth-store/pool bypass, auxiliary/usage paths, same-principal retry, final endpoint guards and frozen policy are implemented. Independent review cleared the final diff. The canonical new regression file passes24/24. An earlier seven-file provider/auth/auxiliary suite passed384/384; the extraction regression suite passed270/270, including the Windows-safe decoded consent-path assertion and all23 session-policy tests. The final lock regression passes24/24. Ruff, the actual pre-commit hook and diff checks pass. Final commit-artifact blocking checks are pending. Live activation and actual model/tool/delivery evidence are pending.

No credentials, account identifiers or operating configuration belong in this repository. Activation remains profile-scoped; ordinary provider defaults are unchanged.

Required file caps were met by extracting existing client construction, auxiliary credentials and API selection into topical siblings with late-bound facade seams. Final independent review cleared the extracted guards and explicit-lock priority. Untracked test-generated directories are preserved and excluded from the published commit.

## Merged bootstrap preparation record

Active mission: [Fork CI publishing guards](docs/missions/2026-11-20-fork-ci-publishing-guards.md).

This isolated branch is based on fork main `eaac327fac2c`. It contains only
fork-specific workflow exclusions and documentation, not runtime PR1's changes.
Root authorised a guard-only bootstrap merge after independent review and local
canonical/static checks, because online CI is paused and no required remote
bootstrap check exists. Default main must contain the verified guards before
repository-wide Actions restoration. No runtime release is authorised by this exception.

Runtime PR1 remains separate at `4ae5694f5e`; its real current-head macOS and
aggregate checks are mandatory before runtime merge. Preserve unrelated work and
the protected untracked directories in the runtime worktree.

Candidate verification: independent SHIP, 10,752 semantic contexts, 17 local checks
and two workflow-graph tests passed. Routing coverage passed 104 cases initially;
one Bash startup timeout was covered by a passing isolated 32-case matrix retry.
Online CI is explicitly unavailable for the guard-only bootstrap. Publish/read back
the precise guard PR before its authorised merge, then verify main before restoration.
