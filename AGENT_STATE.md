# Active bounded integration

Mission: [Codex CLI access source](docs/missions/2026-11-19-codex-cli-access-source.md).

The opt-in access-only source preserves the native tool loop. Auth-store/pool bypass, auxiliary/usage paths, same-principal retry, final endpoint guards and frozen policy are implemented. Independent review cleared the final diff. The canonical new regression file passes24/24. An earlier seven-file provider/auth/auxiliary suite passed384/384; the expanded final run is in progress. Ruff and diff checks pass. Live activation and actual model/tool/delivery evidence are pending.

No credentials, account identifiers or operating configuration belong in this repository. Activation remains profile-scoped; ordinary provider defaults are unchanged.
