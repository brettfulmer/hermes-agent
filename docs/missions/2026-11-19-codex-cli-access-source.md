# Mission: opt-in use of the existing Codex CLI access session

Status: IN PROGRESS. This is a bounded integration fix: an already authenticated Codex CLI can be healthy while Hermes' independent OAuth store is expired.

Keep Hermes' native conversation, tools and approval loop. Add an explicit per-profile credential-source option that reads only a current CLI-owned access token, without adopting, persisting or refreshing its grant. Default behaviour remains the independent Hermes store. Pin shared access to the official Codex endpoint and fail closed on conflicting overrides, missing/invalid/expired sessions or mismatched account metadata.

Done: isolated regressions prove bypass of stale stores/pools, no credential writes/refresh/fallback, endpoint constraints and unchanged opted-out behaviour. Independent review and the repository's required checks precede activation. A live deployment requires provider evidence, existing tool execution, cancellation and reviewed delivery; offline tests alone are not that proof.
