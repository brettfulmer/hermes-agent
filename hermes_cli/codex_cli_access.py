"""Read-only, explicitly selected access to the Codex CLI's current session.

The CLI owns its refresh grant. This module never adopts, writes or refreshes it.
"""
from __future__ import annotations

import json
import copy
import math
import os
import time
from pathlib import Path
from typing import Any

from hermes_cli.auth_constants import DEFAULT_CODEX_BASE_URL, _codex_err, _decode_jwt_claims


def source_config() -> dict[str, Any]:
    from hermes_cli import runtime_provider
    context = getattr(runtime_provider, "_FROZEN_RUNTIME_CONFIG", None)
    frozen = context.get() if context is not None else None
    if frozen is not None:
        return copy.deepcopy(frozen)
    from hermes_cli.config import load_config_readonly
    return load_config_readonly()


def selected(config: dict[str, Any] | None = None) -> bool:
    cfg = source_config() if config is None else config
    section = cfg.get("codex_oauth") or {}
    source = section.get("credential_source", "hermes") if isinstance(section, dict) else None
    if source not in {"hermes", "codex_cli"}:
        raise _codex_err("codex_oauth.credential_source must be hermes or codex_cli.", "codex_auth_source_invalid", relogin=False)
    return source == "codex_cli"


def resolve(*, explicit_api_key=None, explicit_base_url=None, model_config=None) -> dict[str, Any]:
    cfg = source_config()
    model = model_config if model_config is not None else cfg.get("model") or {}
    model = model if isinstance(model, dict) else {}
    official = DEFAULT_CODEX_BASE_URL.rstrip("/")
    from agent.secret_scope import get_secret_str
    endpoints = [explicit_base_url, model.get("base_url"), get_secret_str("HERMES_CODEX_BASE_URL", "")]
    if explicit_api_key or any(value and str(value).rstrip("/") != official for value in endpoints):
        raise _codex_err("CLI-owned Codex access requires the official Codex endpoint and no API-key override.", "codex_cli_route_conflict", relogin=False)
    if model.get("openai_runtime") not in {None, "", "auto"}:
        raise _codex_err("CLI-owned access uses the native Codex Responses transport; remove the conflicting runtime override.", "codex_cli_runtime_conflict", relogin=False)
    path = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser() / "auth.json"
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Oversized cache")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        tokens = data.get("tokens") or {}
        access = tokens.get("access_token")
        if data.get("auth_mode") != "chatgpt" or not isinstance(access, str) or not access:
            raise ValueError("No ChatGPT access")
        claims = _decode_jwt_claims(access)
        expiry = claims.get("exp")
        if not isinstance(expiry, (int, float)) or not math.isfinite(expiry) or expiry <= time.time() + 60:
            raise ValueError("Expired or unknown expiry")
        account = (claims.get("https://api.openai.com/auth") or {}).get("chatgpt_account_id")
        if not isinstance(account, str) or not account or (tokens.get("account_id") and tokens["account_id"] != account):
            raise ValueError("Account metadata mismatch")
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        raise _codex_err("The Codex CLI ChatGPT session is missing, invalid or expired. Open Codex or run `codex login`, then retry the same job. Hermes did not copy or refresh its grant.", "codex_cli_auth_unavailable", relogin=True) from None
    return {"provider": "openai-codex", "api_key": access, "base_url": official,
            "source": "codex-cli-session", "last_refresh": None, "auth_mode": "chatgpt", "account_id": account}


def for_existing_access(previous: str, *, base_url=None) -> dict[str, Any]:
    """Retry with current CLI access only when its user/workspace identity stayed the same."""
    current = resolve(explicit_base_url=base_url)
    if previous and previous != current["api_key"]:
        def identity(token):
            claims = _decode_jwt_claims(token)
            auth = claims.get("https://api.openai.com/auth") or {}
            account = auth.get("chatgpt_account_id") if isinstance(auth, dict) else None
            return (claims.get("sub"), account)
        old, new = identity(previous), identity(current["api_key"])
        if not all(isinstance(v, str) and v for v in old + new) or old != new:
            raise _codex_err("The Codex CLI account changed; this running job cannot switch accounts automatically.", "codex_cli_account_changed", relogin=False)
    return current


def validate_transport(*, api_key, base_url, provider=None) -> None:
    """Final check after route overlays, before any SDK client can send the bearer."""
    if not selected():
        return
    claims = _decode_jwt_claims(api_key) if isinstance(api_key, str) else {}
    oauth = claims.get("https://api.openai.com/auth") or {}
    is_codex_access = isinstance(oauth, dict) and bool(oauth.get("chatgpt_account_id"))
    if provider == "openai-codex" or is_codex_access:
        if provider and provider != "openai-codex":
            raise _codex_err("CLI-owned Codex access cannot be sent through another provider.", "codex_cli_route_conflict", relogin=False)
        if not isinstance(api_key, str) or not api_key.strip():
            raise _codex_err("CLI-owned Codex access is missing; no environment credential was substituted.", "codex_cli_auth_unavailable", relogin=True)
        for_existing_access(api_key, base_url=base_url)


def validate_route(route: dict, runtime: dict) -> None:
    """Check only route overrides actually applied by the native API precedence chain."""
    if runtime.get("provider") == "openai-codex" and selected():
        resolve(explicit_api_key=route.get("api_key"), explicit_base_url=route.get("base_url"))
