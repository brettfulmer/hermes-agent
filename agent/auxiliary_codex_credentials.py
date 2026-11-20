"""Codex auxiliary credential authority; facade calls remain late-bound."""
from typing import Optional


def _resolve_codex_credential_and_base(model: Optional[str] = None) -> tuple[Optional[str], str]:
    """``(token, base_url)`` taken from ONE authority, so a Codex key is only ever sent to the host
    it belongs to (#121486): the profile-scoped ``HERMES_CODEX_BASE_URL`` wins; otherwise a pooled
    key goes where that pool entry routes (row URL / ``model.base_url``) and the auth.json OAuth
    token goes to the ChatGPT default. ``(None, <base>)`` without a usable token."""
    from agent import auxiliary_client as origin
    from hermes_cli import codex_cli_access
    if codex_cli_access.selected():
        creds = codex_cli_access.resolve()
        return creds["api_key"], creds["base_url"]
    override = origin._codex_base_url_override()
    pool_present, entry = origin._select_pool_entry("openai-codex", model)  # a model-scoped cooldown spares siblings
    if pool_present:
        token = origin._pool_runtime_api_key(entry)
        if token:
            if override:
                return token, override
            # Same route rule as the chat path (row URL, else ``model.base_url``); never empty.
            from hermes_cli.auth_codex import _codex_pool_route_base_url
            return token, _codex_pool_route_base_url(origin._pool_runtime_base_url(entry))
    # No usable pool token: auth.json only (re-selecting could pair another row's key with the default).
    return origin._read_codex_singleton_token(), override or origin._CODEX_AUX_BASE_URL


def _read_codex_singleton_token() -> Optional[str]:
    """The profile's auth.json Codex access token (expired JWTs skipped), else None."""
    from agent import auxiliary_client as origin
    from hermes_cli.auth_constants import AuthError
    try:
        from hermes_cli.auth import _read_codex_tokens
        access_token = _read_codex_tokens().get("tokens", {}).get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            return None
        # Expired JWTs would block the auto chain and prevent fallback to working providers.
        try:
            import base64
            payload = access_token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            exp = origin.json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0)
            if exp and origin.time.time() > exp:
                origin.logger.debug("Codex access token expired (exp=%s), skipping", exp)
                return None
        except (ValueError, TypeError, IndexError, AttributeError):
            origin.logger.debug("Codex auxiliary access is opaque; preserving the existing credential path", exc_info=True)
        return access_token.strip()
    except (AuthError, OSError, ValueError, TypeError, AttributeError) as exc:
        origin.logger.debug("Could not read Codex auth for auxiliary client: %s", exc)
        return None

