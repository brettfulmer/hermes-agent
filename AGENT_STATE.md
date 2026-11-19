# Active bounded integration

Mission: [Codex CLI access source](docs/missions/2026-11-19-codex-cli-access-source.md).

The opt-in access-only source preserves the native tool loop. Auth-store/pool bypass, auxiliary/usage paths, same-principal retry, final endpoint guards and frozen policy are implemented. Independent review cleared the final diff. The canonical new regression file passes24/24. An earlier seven-file provider/auth/auxiliary suite passed384/384; the extraction regression suite passed270/270, including the Windows-safe decoded consent-path assertion and all23 session-policy tests. The final lock regression passes24/24. Ruff, the actual pre-commit hook and diff checks pass. Final commit-artifact blocking checks are pending. Live activation and actual model/tool/delivery evidence are pending.

No credentials, account identifiers or operating configuration belong in this repository. Activation remains profile-scoped; ordinary provider defaults are unchanged.

Required file caps were met by extracting existing client construction, auxiliary credentials and API selection into topical siblings with late-bound facade seams. Final independent review cleared the extracted guards and explicit-lock priority. Untracked test-generated directories are preserved and excluded from the published commit.
