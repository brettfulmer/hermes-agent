# Use the existing Codex CLI login

Hermes normally owns an independent Codex OAuth grant. For a profile that should use the current file-backed Codex CLI ChatGPT session instead, set:

```yaml
codex_oauth:
  credential_source: codex_cli
```

Keep the existing `openai-codex` provider and model selection. The native Hermes conversation, tools and approvals continue to run normally. This option does not activate the app-server runtime or migrate global Codex configuration.

The CLI remains the sole owner of its refresh grant. Hermes reads a valid access token from the CLI's `auth.json` under `CODEX_HOME` (otherwise `~/.codex`). It never imports the pair into Hermes, writes either auth store, or invokes token refresh. Keyring-only sessions are not supported by this reader. Missing, malformed, mismatched or near-expiry access fails with a `codex login` instruction.

Access is pinned to the official Codex Responses endpoint. Conflicting API-key, endpoint and app-server overrides are refused, including API route overlays and final client construction. A retry can adopt access already updated by the CLI only for the same user and workspace. Frozen sessions retain their source; sessions intentionally following their profile adopt source changes with model changes.

Credential source and provider fallback are separate settings. For a Codex-only workflow, remove both `fallback_providers` and legacy `fallback_model` choices, including any external policy that rewrites them. Other profiles keep the independent Hermes source by default (`credential_source: hermes`).

Verify actual provider, tool execution and result delivery after activation. A configured source or successful cache read alone is not proof of a working conversation.
