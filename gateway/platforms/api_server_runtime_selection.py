"""Native API model/session precedence, called from the API adapter facade."""
from typing import Optional, Any
from importlib import import_module
from functools import partial
from hermes_cli.codex_cli_access import validate_route


def _origin_call(name, *args, **kwargs):
    return getattr(import_module("gateway.platforms.api_server"), name)(*args, **kwargs)


class _OriginLogger:
    def __getattr__(self, name):
        return getattr(import_module("gateway.platforms.api_server").logger, name)


_clean_request_string = partial(_origin_call, "_clean_request_string")
_apply_runtime_agent_overrides = partial(_origin_call, "_apply_runtime_agent_overrides")
logger = _OriginLogger()


def _route_after_lock(route, requested_model, confirmed):
    # A lock-only caller may carry its selection in route; an explicit locked model wins.
    return None if confirmed and requested_model else route


def _select_agent_runtime(
    self, runtime_kwargs: dict[str, Any], model: str, *, requested_model: Optional[str],
    requested_provider: Optional[str], route: Optional[dict[str, Any]], session_model: Optional[str],
    confirmed_runtime_lock: bool, gateway_session_key: Optional[str], session_id: Optional[str]) -> tuple:
    """Apply the model/provider precedence chain for one agent (mutates ``runtime_kwargs``):
    confirmed Browser lock > session ``/model`` override > session-persisted model >
    model_routes alias > per-request provider/model > global defaults. A confirmed lock
    bypasses the override and fails closed if its provider cannot be resolved.
    Returns ``(model, session_override, request_model, request_provider)``."""
    request_model = _clean_request_string(requested_model)
    request_provider = _clean_request_string(requested_provider)
    route = _route_after_lock(route, request_model, confirmed_runtime_lock)
    route_cfg = route if isinstance(route, dict) else {}
    route_model = _clean_request_string(route_cfg.get("model"))
    route_provider = _clean_request_string(route_cfg.get("provider"))
    session_key = gateway_session_key or session_id
    session_row_model = _clean_request_string(session_model)
    current_provider = _clean_request_string(runtime_kwargs.get("provider"))
    session_override = None if confirmed_runtime_lock else self._session_model_override_for(session_key)
    # Model-string precedence (override > session-persisted > global) is owned by
    # hermes_cli.model_switch.resolve_effective_model.
    from hermes_cli.model_switch import resolve_effective_model
    if session_override:
        model = resolve_effective_model(session_override, None, model)
        self._apply_provider_runtime(
            runtime_kwargs,
            _clean_request_string(session_override.get("provider")) or current_provider,
            target_model=model)
        _apply_runtime_agent_overrides(runtime_kwargs, session_override)
        if route or request_model or request_provider:
            logger.debug(
                "api_server request selection skipped: session /model override wins for %s",
                session_key or "")
    elif session_row_model and not confirmed_runtime_lock:
        # A session-persisted raw model (no route alias) is a standing selection that pins
        # this session's turns ahead of per-request body values.
        self._apply_provider_runtime(
            runtime_kwargs, current_provider, target_model=session_row_model)
        model = resolve_effective_model(None, session_row_model, model)
        if request_model or request_provider:
            logger.debug(
                "api_server request selection skipped: session-persisted model wins for %s",
                session_key or "")
    else:
        # The request's ``model`` selected the route, so its value is the ALIAS — never a
        # model name; a route with no ``model`` key keeps the global default.
        effective_model = (route_model or model) if route is not None else (request_model or model)
        effective_provider = request_provider or route_provider or current_provider
        applied = False
        if effective_provider and (bool(request_provider or route_provider) or effective_model != model):
            # A confirmed Browser lock fails closed: never fall through to the previous
            # global provider's credentials.
            applied = self._apply_provider_runtime(
                runtime_kwargs, effective_provider, target_model=effective_model,
                required=bool(request_provider) or confirmed_runtime_lock)
        if not applied and effective_provider and effective_provider != current_provider:
            runtime_kwargs["provider"] = effective_provider
        model = effective_model
        # Per-route explicit transport secrets/base URLs win after provider resolution.
        validate_route(route_cfg, runtime_kwargs)
        for key in ("api_key", "base_url"):
            value = _clean_request_string(route_cfg.get(key))
            if value:
                runtime_kwargs[key] = value
        if route:
            logger.debug(
                "api_server request selection applied: model=%s provider=%s route_provider=%s request_provider=%s",
                model, runtime_kwargs.get("provider"), route_provider or "", request_provider or "")
    model = self._recover_or_record_model(model, runtime_kwargs, gateway_session_key)
    return model, session_override, request_model, request_provider

