"""Provider-auth defaults. Pure data; no credential or config reads."""
PROVIDER_AUTH_DEFAULTS = {
    "providers": {},
    "credential_pool_strategies": {},
    # Opt-in only: the CLI remains the owner of its refresh grant.
    "codex_oauth": {"credential_source": "hermes"},
}
