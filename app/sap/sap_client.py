from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SAPODataError(Exception):
    def __init__(
        self,
        status_code: int | None,
        message: str,
        sap_error_code: str | None = None,
        sap_error_message: str | None = None,
        response_body: dict | str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.sap_error_code = sap_error_code
        self.sap_error_message = sap_error_message
        self.response_body = response_body

    def __repr__(self) -> str:
        return (
            f"SAPODataError(status_code={self.status_code}, "
            f"sap_error_code={self.sap_error_code!r}, message={self.message!r})"
        )


def _parse_sap_error(response: httpx.Response) -> tuple[str | None, str | None, dict | str | None]:
    """Return (sap_error_code, sap_error_message, body). Never raises."""
    try:
        body = response.json()
    except Exception:
        text = response.text[:500] if response.text else None
        return None, text, text

    error_obj = body.get("error", {})
    code = error_obj.get("code")
    msg_obj = error_obj.get("message", {})
    if isinstance(msg_obj, dict):
        msg = msg_obj.get("value")
    else:
        msg = str(msg_obj) if msg_obj else None
    return code, msg, body


class SAPODataClient:
    def __init__(
        self,
        base_url: str,
        auth_type: str,
        user: str | None,
        password: str | None,
        bearer_token: str | None,
        sap_client: str | None,
        verify_ssl: bool,
        timeout_seconds: int,
    ):
        self._base_url = base_url.rstrip("/")
        self._auth_type = auth_type
        self._sap_client = sap_client or ""
        self._timeout = timeout_seconds
        self._csrf_cache: dict[str, str] = {}

        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if auth_type == "bearer":
            # Header set here; never logged
            headers["Authorization"] = f"Bearer {bearer_token}"
            self._client = httpx.Client(
                headers=headers,
                verify=verify_ssl,
                timeout=timeout_seconds,
            )
        else:
            self._client = httpx.Client(
                auth=(user, password) if user and password else None,
                headers=headers,
                verify=verify_ssl,
                timeout=timeout_seconds,
            )

    def _base_params(self) -> dict[str, str]:
        params: dict[str, str] = {"$format": "json"}
        if self._sap_client:
            params["sap-client"] = self._sap_client
        return params

    def get(self, service_path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self._base_url}/{service_path.lstrip('/')}"
        merged = {**self._base_params(), **(params or {})}
        logger.info("SAP GET %s params=%s", url, {k: v for k, v in merged.items() if k != "sap-client"})
        try:
            resp = self._client.get(url, params=merged)
        except httpx.RequestError as exc:
            raise SAPODataError(None, f"Network error on GET {url}: {exc}") from exc
        self._raise_for_status(resp)
        return resp.json()

    def fetch_csrf_token(self, service_root: str) -> str:
        url = f"{self._base_url}/{service_root.lstrip('/')}"
        params = self._base_params()
        logger.info("Fetching X-CSRF-Token from %s", url)
        try:
            resp = self._client.get(url, headers={"X-CSRF-Token": "Fetch"}, params=params)
        except httpx.RequestError as exc:
            raise SAPODataError(None, f"Network error fetching CSRF token: {exc}") from exc
        token = resp.headers.get("x-csrf-token") or resp.headers.get("X-CSRF-Token")
        if not token:
            raise SAPODataError(resp.status_code, "No X-CSRF-Token in SAP response headers")
        # Cache per service root
        self._csrf_cache[service_root] = token
        logger.info("CSRF token fetched and cached for service root %s", service_root)
        return token

    def post(
        self,
        service_root: str,
        entity_path: str,
        payload: dict,
        params: dict[str, Any] | None = None,
    ) -> dict:
        token = self._csrf_cache.get(service_root) or self.fetch_csrf_token(service_root)
        url = f"{self._base_url}/{entity_path.lstrip('/')}"
        merged = {**self._base_params(), **(params or {})}
        logger.info("SAP POST %s", url)

        try:
            resp = self._client.post(
                url,
                json=payload,
                params=merged,
                headers={"X-CSRF-Token": token},
            )
        except httpx.RequestError as exc:
            raise SAPODataError(None, f"Network error on POST {url}: {exc}") from exc

        if resp.status_code == 403:
            # CSRF token may have expired — refetch once and retry
            logger.warning("SAP POST 403 — refetching CSRF token and retrying once")
            token = self.fetch_csrf_token(service_root)
            try:
                resp = self._client.post(
                    url,
                    json=payload,
                    params=merged,
                    headers={"X-CSRF-Token": token},
                )
            except httpx.RequestError as exc:
                raise SAPODataError(None, f"Network error on POST retry {url}: {exc}") from exc

        self._raise_for_status(resp)
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    def ping(self) -> dict:
        url = f"{self._base_url}/API_MATERIAL_DOCUMENT_SRV/$metadata"
        merged = self._base_params()
        logger.info("SAP ping %s", url)
        try:
            resp = self._client.get(url, params=merged)
        except httpx.RequestError as exc:
            return {"reachable": False, "error": str(exc)}
        return {"reachable": resp.status_code < 500, "status_code": resp.status_code}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        code, sap_msg, body = _parse_sap_error(resp)
        raise SAPODataError(
            status_code=resp.status_code,
            message=f"SAP OData error {resp.status_code}",
            sap_error_code=code,
            sap_error_message=sap_msg,
            response_body=body,
        )
