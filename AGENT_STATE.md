# Fork CI restoration configuration

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
