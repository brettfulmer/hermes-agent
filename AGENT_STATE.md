# Active bounded integration

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
