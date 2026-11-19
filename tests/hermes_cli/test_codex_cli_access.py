"""The explicit CLI access source must never consume or persist its refresh grant."""
import base64
import json
import time
from unittest import mock

import pytest

from hermes_cli import auth_codex, codex_cli_access, runtime_provider
from hermes_cli.auth_constants import AuthError, DEFAULT_CODEX_BASE_URL
_actual_source_config = codex_cli_access.source_config


def jwt(**changes):
    claims = {"sub": "fixture-user", "exp": time.time() + 3600, "https://api.openai.com/auth": {"chatgpt_account_id": "fixture-account"}}
    claims.update(changes)
    encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"fixture.{encoded}.signature"


@pytest.fixture
def cli_source(tmp_path, monkeypatch):
    cfg = {"codex_oauth": {"credential_source": "codex_cli"}, "model": {"provider": "openai-codex", "default": "gpt-6-sol"}}
    monkeypatch.setattr(codex_cli_access, "source_config", lambda: cfg)
    monkeypatch.setattr(runtime_provider, "_get_model_config", lambda: cfg["model"])
    cli_home = tmp_path / "cli"
    cli_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(cli_home))
    monkeypatch.delenv("OPENAI_CODEX_BASE_URL", raising=False)
    monkeypatch.delenv("HERMES_CODEX_BASE_URL", raising=False)
    path = cli_home / "auth.json"
    path.write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {"access_token": jwt(), "account_id": "fixture-account", "refresh_token": "DO-NOT-ADOPT"}}))
    return cfg, path


def test_valid_access_bypasses_native_store_pool_and_refresh(cli_source):
    cfg, path = cli_source
    before = path.read_bytes()
    with mock.patch("hermes_cli.auth._read_codex_tokens", side_effect=AssertionError("native store")), mock.patch.object(runtime_provider, "load_pool", side_effect=AssertionError("pool")), mock.patch.object(auth_codex, "refresh_codex_oauth_pure", side_effect=AssertionError("refresh")):
        result = auth_codex.resolve_codex_runtime_credentials(force_refresh=True)
        assert result["source"] == "codex-cli-session"
        assert result["base_url"] == DEFAULT_CODEX_BASE_URL.rstrip("/")
        assert "refresh_token" not in result
        assert "DO-NOT-ADOPT" not in json.dumps(result)
        assert runtime_provider._resolve_from_pool("openai-codex", "openai-codex", cfg["model"], None, None, None) is None
    assert path.read_bytes() == before
    assert list(path.parent.iterdir()) == [path]


def test_full_runtime_resolution_uses_native_responses_without_ladder(cli_source):
    with mock.patch.object(runtime_provider, "_ladder_rungs", side_effect=AssertionError("credential ladder")):
        runtime = runtime_provider.resolve_runtime_provider(requested="openai-codex", target_model="gpt-6-sol")
    assert runtime["provider"] == "openai-codex"
    assert runtime["api_mode"] == "codex_responses"
    assert runtime["source"] == "codex-cli-session"


@pytest.mark.parametrize("claims", [{"exp": 1}, {"exp": time.time() + 10}, {"exp": None}, {"exp": float("inf")}, {"https://api.openai.com/auth": {}}, {"https://api.openai.com/auth": {"chatgpt_account_id": "another-account"}}])
def test_invalid_expiry_or_account_fails_closed(cli_source, claims):
    _, path = cli_source
    data = json.loads(path.read_text()); data["tokens"]["access_token"] = jwt(**claims)
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    with pytest.raises(AuthError, match="codex login"):
        auth_codex.resolve_codex_runtime_credentials(force_refresh=True)
    assert path.read_bytes() == before


@pytest.mark.parametrize("contents", [None, "not JSON", "[]", '{"auth_mode":"apikey","tokens":{}}'])
def test_missing_or_malformed_cli_session_fails_closed(cli_source, contents):
    _, path = cli_source
    if contents is None:
        path.unlink()
    else:
        path.write_text(contents)
    with pytest.raises(AuthError, match="codex login"):
        auth_codex.resolve_codex_runtime_credentials()


@pytest.mark.parametrize("override", [{"explicit_api_key": "unrelated-key"}, {"explicit_base_url": "https://other.example"}])
def test_explicit_credential_destination_overrides_are_refused(cli_source, override):
    with pytest.raises(AuthError, match="official Codex endpoint"):
        runtime_provider.resolve_runtime_provider(requested="openai-codex", **override)


def test_profile_custom_endpoint_and_transport_are_refused(cli_source):
    cfg, _ = cli_source
    cfg["model"]["base_url"] = "https://other.example"
    with pytest.raises(AuthError, match="official Codex endpoint"):
        codex_cli_access.resolve()
    cfg["model"].pop("base_url"); cfg["model"]["openai_runtime"] = "codex_app_server"
    with pytest.raises(AuthError, match="native Codex Responses"):
        codex_cli_access.resolve()


def test_opted_out_profile_retains_independent_auth_resolution(cli_source):
    cfg, _ = cli_source
    cfg["codex_oauth"]["credential_source"] = "hermes"
    assert not codex_cli_access.selected()
    with mock.patch.object(runtime_provider, "_ladder_rungs", return_value=iter([{"provider": "openai-codex", "api_mode": "codex_responses", "api_key": "independent", "base_url": DEFAULT_CODEX_BASE_URL}])) as ladder:
        result = runtime_provider.resolve_runtime_provider(requested="openai-codex")
    assert result["api_key"] == "independent"
    ladder.assert_called_once()


def test_auxiliary_and_usage_paths_do_not_select_or_refresh_a_native_pool(cli_source):
    from agent import auxiliary_client, account_usage
    with mock.patch.object(auxiliary_client, "_select_pool_entry", side_effect=AssertionError("pool")), mock.patch("agent.credential_pool.load_pool", side_effect=AssertionError("pool")), mock.patch.object(account_usage, "_read_codex_tokens", side_effect=AssertionError("native store")):
        token, base = auxiliary_client._resolve_codex_credential_and_base()
        assert token and base == DEFAULT_CODEX_BASE_URL.rstrip("/")
        current, _, account = account_usage._resolve_codex_usage_credentials(base, token, force_refresh=True)
        assert current == token and account == "fixture-account"


def test_retry_reads_a_new_cli_access_token_but_never_switches_principal(cli_source):
    _, path = cli_source
    before = codex_cli_access.resolve()["api_key"]
    data = json.loads(path.read_text()); data["tokens"]["access_token"] = jwt(exp=time.time() + 7200)
    path.write_text(json.dumps(data))
    assert codex_cli_access.for_existing_access(before)["api_key"] != before
    data["tokens"]["access_token"] = jwt(sub="different-user")
    path.write_text(json.dumps(data))
    with pytest.raises(AuthError, match="cannot switch accounts"):
        codex_cli_access.for_existing_access(before)


def test_401_recovery_adopts_only_cli_updated_access_in_memory(cli_source):
    from types import SimpleNamespace
    from agent.client_lifecycle import ClientLifecycleMixin
    _, path = cli_source
    previous = codex_cli_access.resolve()["api_key"]
    adopt = mock.Mock(return_value=True)
    client = SimpleNamespace(api_mode="codex_responses", provider="openai-codex", api_key=previous,
                             base_url=DEFAULT_CODEX_BASE_URL, _adopt_openai_credentials=adopt)
    assert not ClientLifecycleMixin._try_refresh_codex_client_credentials(client)
    data = json.loads(path.read_text()); data["tokens"]["access_token"] = jwt(exp=time.time() + 7200)
    path.write_text(json.dumps(data))
    with mock.patch("hermes_cli.auth.resolve_codex_runtime_credentials", side_effect=AssertionError("native refresh")):
        assert ClientLifecycleMixin._try_refresh_codex_client_credentials(client)
    adopt.assert_called_once_with(data["tokens"]["access_token"], DEFAULT_CODEX_BASE_URL.rstrip("/"), reason="codex_cli_access_updated")
    data["tokens"]["access_token"] = jwt(sub="different-user"); path.write_text(json.dumps(data))
    adopt.reset_mock()
    assert not ClientLifecycleMixin._try_refresh_codex_client_credentials(client)
    adopt.assert_not_called()


def test_real_profile_configuration_selects_cli_without_auth_store_writes(cli_source, tmp_path, monkeypatch):
    cfg, _ = cli_source
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text(json.dumps(cfg))
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(codex_cli_access, "source_config", _actual_source_config)
    assert codex_cli_access.selected()
    assert auth_codex.resolve_codex_runtime_credentials()["source"] == "codex-cli-session"
    assert not (home / "auth.json").exists()
    assert not (home / "auth.lock").exists()


@pytest.mark.parametrize("frozen_source,live_source,expected", [("hermes", "codex_cli", False), ("codex_cli", "hermes", True)])
def test_frozen_source_wins_over_live_profile(cli_source, monkeypatch, frozen_source, live_source, expected):
    from hermes_cli import config
    monkeypatch.setattr(config, "load_config_readonly", lambda: {"codex_oauth": {"credential_source": live_source}})
    monkeypatch.setattr(codex_cli_access, "source_config", _actual_source_config)
    with runtime_provider.frozen_runtime_config({"codex_oauth": {"credential_source": frozen_source}}):
        assert codex_cli_access.selected() is expected


def test_actual_api_route_selection_rejects_post_resolution_endpoint_override(cli_source):
    from types import SimpleNamespace
    from gateway.platforms.api_server import APIServerAdapter
    token = codex_cli_access.resolve()["api_key"]
    actor = SimpleNamespace(_session_model_override_for=lambda key: None,
                            _recover_or_record_model=lambda model, kwargs, key: model)
    def apply(kwargs, provider, **ignored):
        kwargs.update(provider=provider, api_key=token, base_url=DEFAULT_CODEX_BASE_URL)
        return True
    actor._apply_provider_runtime = apply
    with pytest.raises(AuthError, match="official Codex endpoint"):
        APIServerAdapter._select_agent_runtime(actor, {"provider": "openai-codex", "api_key": token}, "gpt-6-sol",
            requested_model=None, requested_provider=None, route={"provider": "openai-codex", "model": "gpt-6-sol", "base_url": "https://other.example"},
            session_model=None, confirmed_runtime_lock=False, gateway_session_key=None, session_id="fixture")
    # An explicit lock ignores a stale route. Its unused override must not veto that lock.
    current = {"provider": "openai-codex", "api_key": token, "base_url": DEFAULT_CODEX_BASE_URL}
    result = APIServerAdapter._select_agent_runtime(actor, current, "gpt-6-sol", requested_model="gpt-6.2", requested_provider="openai-codex",
        route={"provider": "openai-codex", "model": "stale-route-model", "base_url": "https://unused.example"}, session_model=None,
        confirmed_runtime_lock=True, gateway_session_key=None, session_id="fixture")
    assert current["base_url"] == DEFAULT_CODEX_BASE_URL
    assert result[0] == "gpt-6.2"


def test_final_main_and_auxiliary_client_factories_refuse_foreign_destination(cli_source):
    from types import SimpleNamespace
    from agent import agent_runtime_helpers, auxiliary_client
    token = codex_cli_access.resolve()["api_key"]
    actor = SimpleNamespace(provider="openai-codex")
    with pytest.raises(AuthError, match="official Codex endpoint"):
        agent_runtime_helpers.create_openai_client(actor, {"api_key": token, "base_url": "https://other.example"}, reason="fixture", shared=False)
    with pytest.raises(AuthError, match="official Codex endpoint"):
        auxiliary_client._create_openai_client(api_key=token, base_url="https://other.example")
    with pytest.raises(AuthError, match="another provider"):
        codex_cli_access.validate_transport(api_key=token, base_url="https://other.example", provider="custom")
