from __future__ import annotations

import json

import httpx
import pytest

from app.sap.sap_client import SAPODataClient, SAPODataError


def _make_client(
    transport: httpx.MockTransport,
    auth_type: str = "basic",
    user: str = "testuser",
    password: str = "testpass",
    bearer_token: str | None = None,
    sap_client: str = "100",
) -> SAPODataClient:
    client = SAPODataClient(
        base_url="https://sap.example.com/sap/opu/odata/sap",
        auth_type=auth_type,
        user=user,
        password=password,
        bearer_token=bearer_token,
        sap_client=sap_client,
        verify_ssl=False,
        timeout_seconds=10,
    )
    # Inject mock transport
    client._client = httpx.Client(transport=transport, verify=False)
    return client


def _json_response(body: dict, status: int = 200, headers: dict | None = None) -> httpx.Response:
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    return httpx.Response(status, json=body, headers=h)


def test_basic_auth_configuration():
    """Basic auth client is created without raising."""
    client = SAPODataClient(
        base_url="https://sap.example.com/sap/opu/odata/sap",
        auth_type="basic",
        user="user",
        password="pass",
        bearer_token=None,
        sap_client="100",
        verify_ssl=False,
        timeout_seconds=30,
    )
    assert client._auth_type == "basic"


def test_bearer_auth_header_is_created():
    """Bearer token client stores token in header (not exposed in repr)."""
    client = SAPODataClient(
        base_url="https://sap.example.com/sap/opu/odata/sap",
        auth_type="bearer",
        user=None,
        password=None,
        bearer_token="secret-token",
        sap_client="100",
        verify_ssl=False,
        timeout_seconds=30,
    )
    assert client._auth_type == "bearer"
    # Verify authorization header is in the underlying httpx client
    assert "Authorization" in client._client.headers
    # Should NOT expose token in repr
    assert "secret-token" not in repr(client)


def test_sap_client_param_added():
    """sap-client query parameter is merged into all requests."""
    received_params: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        received_params.append(dict(request.url.params))
        return _json_response({"d": {}})

    transport = httpx.MockTransport(handler)
    client = _make_client(transport, sap_client="200")
    client.get("SOME_SERVICE/EntitySet")
    assert received_params[0].get("sap-client") == "200"


def test_csrf_token_fetched_before_post():
    """POST calls fetch CSRF token first."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("X-CSRF-Token") == "Fetch":
            calls.append("csrf_fetch")
            return httpx.Response(200, headers={"x-csrf-token": "TOKEN123"}, json={})
        if request.method == "POST":
            calls.append("post")
            token = request.headers.get("X-CSRF-Token", "")
            return _json_response({"d": {"MaterialDocument": "5000000001", "MaterialDocumentYear": "2026"}})
        return _json_response({"d": {}})

    transport = httpx.MockTransport(handler)
    client = _make_client(transport)
    client.post("API_MATERIAL_DOCUMENT_SRV/", "API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader", {"data": 1})
    assert "csrf_fetch" in calls
    assert "post" in calls
    assert calls.index("csrf_fetch") < calls.index("post")


def test_csrf_403_triggers_refetch_and_retry():
    """On 403 CSRF error, client refetches token and retries once."""
    call_log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("X-CSRF-Token") == "Fetch":
            call_log.append("fetch")
            return httpx.Response(200, headers={"x-csrf-token": "NEWTOKEN"}, json={})
        if request.method == "POST":
            if len([c for c in call_log if c == "post"]) == 0:
                call_log.append("post")
                return httpx.Response(403, json={"error": {"code": "CSRF", "message": {"value": "Token invalid"}}})
            call_log.append("post_retry")
            return _json_response({"d": {"MaterialDocument": "5000000001", "MaterialDocumentYear": "2026"}})
        return _json_response({"d": {}})

    transport = httpx.MockTransport(handler)
    client = _make_client(transport)
    client.post("API_MATERIAL_DOCUMENT_SRV/", "API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader", {})
    assert call_log.count("fetch") >= 2
    assert "post_retry" in call_log


def test_sap_odata_error_parsed():
    """HTTP 400 with SAP error body is raised as SAPODataError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "MAPI_UNKNOWN_ERROR",
                    "message": {"value": "Quantity exceeds open PO quantity"},
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = _make_client(transport)
    with pytest.raises(SAPODataError) as exc_info:
        client.get("SOME_SERVICE/Entities")
    err = exc_info.value
    assert err.status_code == 400
    assert err.sap_error_code == "MAPI_UNKNOWN_ERROR"
    assert "Quantity" in (err.sap_error_message or "")


def test_credentials_not_in_error_output():
    """SAPODataError repr/str must not contain credentials."""
    err = SAPODataError(
        status_code=401,
        message="Unauthorized",
        sap_error_code="AUTH_FAILED",
        sap_error_message="Invalid credentials",
    )
    err_str = str(err) + repr(err)
    assert "password" not in err_str.lower()
    assert "bearer" not in err_str.lower()


def test_network_error_raises_sap_odata_error():
    """Network-level errors are wrapped in SAPODataError."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    client = _make_client(transport)
    with pytest.raises(SAPODataError):
        client.get("SOME_SERVICE/Entities")
