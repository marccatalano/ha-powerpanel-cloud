"""Client for the official PowerPanel Cloud public API (/public/v1).

Built against CyberPower's published OpenAPI 3.0 spec
(https://powerpanel.cyberpower.com/api/app/openAPI, "PowerPanelCloud API
Document" v1.0.0). Key contract points encoded here:

- Auth: API key sent in the ``Authorization`` header. The spec's examples show
  the bare key; its description says "Bearer Token". We try the bare key first
  (matching the examples) and fall back to a ``Bearer``-prefixed value once on
  401, then remember which form worked.
- PRO accounts: ``GET /public/v1/account`` returns ``IsUsingCloudPro`` and
  ``RegionInfo``. Per the spec, PRO accounts MUST send ``RegionIds`` in request
  bodies and non-PRO accounts MUST NOT.
- Rate limit: 60 calls/minute per endpoint. The coordinator's poll interval
  (default 60s) stays far below this; we surface 429s as retryable errors.

Responses are normalized into the same internal shape the legacy client
produces ({dcode: {"summary": {...}, "details": {...}}}) so the coordinator,
sensors, and user automations are identical regardless of which client backs
the config entry.
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .api import PowerPanelAuthError, PowerPanelConnectionError

_LOGGER = logging.getLogger(__name__)

PUBLIC_API_BASE = "https://iotapi.cyberpower.com/public/v1"

# Official field name -> legacy internal key, per data source dict.
_DETAIL_FIELD_MAP = {
    "OutputVolt": "OutVolt",
    "UpsLoadPct": "LoadPct",
    "UpsLoad": "Load",
    "BatteryHealthIndex": "BHI",
    "PowerRating": "RatPow",
    "PowerSource": "PowSour",
    "ModelName": "Model",
    "FirmwareVersion": "FV",
    "UpsTemperature": "UpsTemperature",  # v2-only sensor
}
_SUMMARY_FIELD_MAP = {
    "BatteryCapacity": "BatCap",
    "BatteryRuntime": "BatRun",
}


class PowerPanelPublicAPIClient:
    """Client for the official PowerPanel Cloud public API."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        self._api_key = api_key.strip()
        self._session = session
        self._auth_value: str | None = None  # resolved working header value
        self._is_pro: bool | None = None
        self._region_ids: list[int] = []

    # ── low-level ─────────────────────────────────────────────────────────────

    def _headers(self, auth_value: str) -> dict:
        return {
            "Authorization": auth_value,
            "Content-Type": "application/json",
        }

    async def _request(
        self, method: str, path: str, payload: dict | None = None
    ) -> Any:
        """Perform a request, resolving the Authorization header form on first use."""
        candidates = (
            [self._auth_value]
            if self._auth_value
            else [self._api_key, f"Bearer {self._api_key}"]
        )
        last_status: int | None = None
        last_body = ""
        for auth_value in candidates:
            try:
                async with self._session.request(
                    method,
                    f"{PUBLIC_API_BASE}{path}",
                    json=payload,
                    headers=self._headers(auth_value),
                ) as resp:
                    raw = await resp.text()
                    if resp.status == 401:
                        last_status, last_body = resp.status, raw[:300]
                        continue  # try the alternate header form
                    if resp.status == 429:
                        raise PowerPanelConnectionError(
                            f"{path}: rate limited (HTTP 429), will retry next cycle"
                        )
                    if resp.status != 200:
                        _LOGGER.error(
                            "%s: HTTP %s from public API: %s",
                            path, resp.status, raw[:300],
                        )
                        raise PowerPanelConnectionError(
                            f"{path}: HTTP {resp.status}: {raw[:300]}"
                        )
                    self._auth_value = auth_value
                    try:
                        return await resp.json(content_type=None)
                    except ValueError as err:
                        _LOGGER.error(
                            "%s: non-JSON response (HTTP %s): %s",
                            path, resp.status, raw[:300],
                        )
                        raise PowerPanelConnectionError(
                            f"{path}: non-JSON response: {raw[:300]}"
                        ) from err
            except aiohttp.ClientError as err:
                raise PowerPanelConnectionError(str(err)) from err
        raise PowerPanelAuthError(
            f"{path}: HTTP {last_status}: invalid API key ({last_body})"
        )

    def _body(self, extra: dict | None = None) -> dict:
        """Build a request body, adding RegionIds only for PRO accounts (per spec)."""
        body: dict = dict(extra or {})
        if self._is_pro and self._region_ids:
            body["RegionIds"] = self._region_ids
        return body

    # ── endpoints ─────────────────────────────────────────────────────────────

    async def authenticate(self) -> bool:
        """Validate the API key and detect account class via /account."""
        data = await self._request("GET", "/account")
        # Response is a list of account objects per the spec example.
        accounts = data if isinstance(data, list) else [data]
        self._is_pro = any(a.get("IsUsingCloudPro") for a in accounts)
        self._region_ids = [
            int(r["Id"])
            for a in accounts
            for r in (a.get("RegionInfo") or [])
            if r.get("Id") is not None
        ]
        _LOGGER.info(
            "Public API account: pro=%s regions=%d", self._is_pro, len(self._region_ids)
        )
        return True

    async def get_devices_info(self) -> list[dict]:
        data = await self._request(
            "POST", "/devices/info/read", self._body()
        )
        return data if isinstance(data, list) else []

    async def get_device_status(self) -> list[dict]:
        data = await self._request(
            "POST", "/devices/status/read", self._body()
        )
        if not isinstance(data, dict):
            return []
        devices: list[dict] = []
        for group in ("DeviceStatus", "SharedDevices", "SharedGroupDevices"):
            entries = data.get(group) or []
            if isinstance(entries, dict):  # schema says object, example says array
                entries = [entries]
            devices.extend(e for e in entries if isinstance(e, dict))
        return devices

    async def get_device_detail(self, sn: str) -> dict | None:
        data = await self._request(
            "POST", "/devices/detail/read", {"sn": sn}
        )
        if isinstance(data, dict):
            return data.get("DeviceStatus") or None
        return None

    async def get_battery_replace(self) -> list[dict]:
        data = await self._request(
            "POST", "/battery/replace/read", self._body()
        )
        return data if isinstance(data, list) else []

    # ── normalization ─────────────────────────────────────────────────────────

    async def async_fetch_data(self) -> dict:
        """Fetch and normalize all device data into the internal shape."""
        if self._is_pro is None:
            await self.authenticate()

        statuses = await self.get_device_status()
        if not statuses:
            raise PowerPanelConnectionError("No device status returned by public API")

        try:
            names = {
                d.get("DeviceSn"): d.get("DeviceName")
                for d in await self.get_devices_info()
            }
        except PowerPanelConnectionError as err:
            _LOGGER.warning("devices/info/read failed, using serials as names: %s", err)
            names = {}

        result: dict = {}
        for status in statuses:
            sn = status.get("DeviceSn")
            dcode = str(status.get("Dcode") or sn or "")
            if not dcode:
                continue

            summary = {
                "device_sn": sn,
                # v2 enum differs from legacy; kept under its own key
                "DeviceStatusV2": status.get("DeviceStatus"),
                "Description": status.get("Description"),
            }

            details: dict = {}
            if sn:
                try:
                    raw_detail = await self.get_device_detail(sn) or {}
                except PowerPanelConnectionError as err:
                    _LOGGER.warning("Detail fetch failed for %s: %s", sn, err)
                    raw_detail = {}
                for official, internal in _DETAIL_FIELD_MAP.items():
                    if official in raw_detail:
                        details[internal] = raw_detail[official]
                for official, internal in _SUMMARY_FIELD_MAP.items():
                    if official in raw_detail:
                        summary[internal] = raw_detail[official]

            if names.get(sn):
                details["DeviceName"] = names[sn]

            result[dcode] = {
                "summary": {k: v for k, v in summary.items() if v is not None},
                "details": details,
            }
        return result

    @property
    def is_pro(self) -> bool | None:
        return self._is_pro
