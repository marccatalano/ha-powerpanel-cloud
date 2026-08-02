"""PowerPanel Cloud API client."""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://iotapi.cyberpower.com"
HMAC_KEY = "cyberpower@TP08!"


def _hash_password(password: str) -> str:
    """Hash password using MD5 + HMAC-SHA512 as used by PowerPanel Cloud web app."""
    pw = password.strip()
    md5 = hashlib.md5(pw.encode()).hexdigest().upper()
    hmac_sha512 = hmac.new(
        HMAC_KEY.encode("utf-8"), pw.encode("utf-8"), hashlib.sha512
    ).hexdigest().upper()
    return md5 + hmac_sha512


class PowerPanelAuthError(Exception):
    """Authentication failed."""


class PowerPanelTwoFactorError(PowerPanelAuthError):
    """Account has two-factor authentication enabled, which is not yet supported."""


class PowerPanelConnectionError(Exception):
    """Connection failed."""


class PowerPanelAPIClient:
    """Client for the PowerPanel Cloud API."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._token: str | None = None
        self._otp: str | None = None
        self._acode: int | None = None
        self._devices: list[dict] = []

    async def authenticate(self) -> bool:
        """Authenticate and store token/otp/acode."""
        hashed = _hash_password(self._password)
        payload = {
            "Account": self._email,
            "Password": hashed,
            "LoginType": 10,
        }
        try:
            async with self._session.post(
                f"{API_BASE}/LoginAccountWithDeviceInfo",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status != 200:
                    raise PowerPanelAuthError(f"HTTP {resp.status}")
                data = await self._parse_json(resp, context="authenticate")
        except aiohttp.ClientError as err:
            raise PowerPanelConnectionError(str(err)) from err

        if not data.get("Flag"):
            raise PowerPanelAuthError("Invalid credentials")

        devices = data.get("DevicesInfor") or []

        # Sanitized shape of the login response — no tokens/keys, just which
        # fields are present. This is the single log line needed to diagnose
        # account-specific failures (issue #1).
        _LOGGER.info(
            "Login response shape: EnableOtp=%s IsMsp=%s RegionId=%s "
            "token_present=%s otpkey_present=%s acode_present=%s devices=%d",
            data.get("EnableOtp"),
            data.get("IsMsp"),
            data.get("RegionId"),
            bool(data.get("token")),
            bool(data.get("OtpKey")),
            data.get("acode") is not None,
            len(devices),
        )

        # The PowerPanel web app branches into a second verification step
        # (/authotp/check) when EnableOtp is true. Without that step the
        # session is not fully activated and subsequent iotapi calls fail.
        if data.get("EnableOtp"):
            raise PowerPanelTwoFactorError(
                "This PowerPanel Cloud account has two-factor authentication "
                "enabled, which this integration does not support yet. "
                "Disable 2FA on the account or wait for 2FA support."
            )

        self._token = data.get("token")
        self._otp = data.get("OtpKey")
        self._devices = devices

        # The web app reads acode directly from the login response
        # (acode: Number(e.acode)) — not from DevicesInfor[0].AccountId.
        raw_acode = data.get("acode")
        if raw_acode is not None:
            try:
                self._acode = int(raw_acode)
            except (TypeError, ValueError):
                _LOGGER.warning("Unparseable acode in login response: %r", raw_acode)
                self._acode = None
        else:
            _LOGGER.warning("Login response contained no acode field")
            self._acode = None

        _LOGGER.debug("Authenticated, acode=%s, devices=%d", self._acode, len(devices))
        return True

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _parse_json(self, resp: aiohttp.ClientResponse, *, context: str) -> dict:
        """Parse a response body as JSON, logging enough detail to diagnose failures.

        The PowerPanel Cloud API doesn't always return JSON on error (empty body,
        an HTML/redirect page, a plain-text message, etc). Previously we called
        resp.json() unconditionally, which threw an unhandled JSONDecodeError and
        crashed the coordinator instead of surfacing something diagnosable.
        """
        raw = await resp.text()
        if not raw.strip():
            _LOGGER.error(
                "%s: empty response body (HTTP %s) from %s",
                context, resp.status, resp.url,
            )
            raise PowerPanelConnectionError(
                f"{context}: empty response body (HTTP {resp.status})"
            )
        try:
            # content_type=None: PowerPanel Cloud doesn't reliably send
            # application/json, so don't let aiohttp reject on that basis.
            return await resp.json(content_type=None)
        except ValueError as err:
            snippet = raw[:300]
            _LOGGER.error(
                "%s: non-JSON response (HTTP %s) from %s: %s",
                context, resp.status, resp.url, snippet,
            )
            raise PowerPanelConnectionError(
                f"{context}: non-JSON response (HTTP {resp.status}): {snippet}"
            ) from err

    async def _post(self, path: str, payload: dict) -> dict:
        """POST to iotapi with Bearer token."""
        try:
            async with self._session.post(
                f"{API_BASE}{path}",
                json=payload,
                headers=self._auth_headers(),
            ) as resp:
                if resp.status == 401:
                    # Token expired, re-authenticate
                    await self.authenticate()
                    async with self._session.post(
                        f"{API_BASE}{path}",
                        json=payload,
                        headers=self._auth_headers(),
                    ) as resp2:
                        return await self._parse_json(resp2, context=path)
                if resp.status != 200:
                    body = (await resp.text())[:300]
                    # Field names + whether each was populated — never values.
                    field_shape = {
                        k: "set" if v not in (None, "") else "MISSING"
                        for k, v in payload.items()
                    }
                    _LOGGER.error(
                        "%s: HTTP %s from PowerPanel Cloud (payload fields: %s): %s",
                        path, resp.status, field_shape, body,
                    )
                    raise PowerPanelConnectionError(f"{path}: HTTP {resp.status}: {body}")
                return await self._parse_json(resp, context=path)
        except aiohttp.ClientError as err:
            raise PowerPanelConnectionError(str(err)) from err

    async def get_device_status(self) -> list[dict]:
        """Get status for all devices (battery %, load, runtime)."""
        # Payload verified against the PowerPanel web app bundle: it sends
        # exactly {account, otp} (plus RegionIds only for MSP region filters).
        # No acode — the beta.2 addition was incorrect and is reverted.
        data = await self._post(
            "/device/read/status",
            {"account": self._email, "otp": self._otp},
        )
        if not data.get("result"):
            _LOGGER.warning(
                "device/read/status returned result=false, full response: %s", data,
            )
            return []
        return data.get("msg", {}).get("device_status", [])

    async def get_device_details(self, dcode: str) -> dict | None:
        """Get full telemetry for a specific device."""
        data = await self._post(
            "/device/read/details",
            {"dcode": int(dcode), "otp": self._otp, "acode": self._acode},
        )
        if not data.get("result"):
            _LOGGER.warning(
                "device/read/details returned result=false for %s, full response: %s",
                dcode, data,
            )
            return None
        return data.get("msg", {}).get("device_status")

    async def get_battery_status(self) -> list[dict]:
        """Get battery replacement info for all devices."""
        data = await self._post(
            "/battery/replace/read",
            {"otp": self._otp, "acode": self._acode},
        )
        if not data.get("result"):
            _LOGGER.warning(
                "battery/replace/read returned result=false, full response: %s", data,
            )
            return []
        return data.get("msg", {}).get("data", [])

    @property
    def devices(self) -> list[dict]:
        """Return device list from last login."""
        return self._devices
