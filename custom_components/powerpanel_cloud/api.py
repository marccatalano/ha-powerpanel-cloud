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
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise PowerPanelConnectionError(str(err)) from err

        if not data.get("Flag"):
            raise PowerPanelAuthError("Invalid credentials")

        self._token = data.get("token")
        self._otp = data.get("OtpKey")
        self._acode = data.get("PackageId")  # acode is AccountId from DevicesInfor
        # Extract acode from first device entry
        devices = data.get("DevicesInfor", [])
        if devices:
            self._acode = devices[0].get("AccountId")
            self._devices = devices
        _LOGGER.debug("Authenticated, acode=%s, devices=%d", self._acode, len(devices))
        return True

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

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
                        return await resp2.json(content_type=None)
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise PowerPanelConnectionError(str(err)) from err

    async def get_device_status(self) -> list[dict]:
        """Get status for all devices (battery %, load, runtime)."""
        data = await self._post(
            "/device/read/status",
            {"account": self._email, "otp": self._otp},
        )
        if not data.get("result"):
            _LOGGER.warning("device/read/status returned result=false")
            return []
        return data.get("msg", {}).get("device_status", [])

    async def get_device_details(self, dcode: str) -> dict | None:
        """Get full telemetry for a specific device."""
        data = await self._post(
            "/device/read/details",
            {"dcode": int(dcode), "otp": self._otp, "acode": self._acode},
        )
        if not data.get("result"):
            _LOGGER.warning("device/read/details returned result=false for %s", dcode)
            return None
        return data.get("msg", {}).get("device_status")

    async def get_battery_status(self) -> list[dict]:
        """Get battery replacement info for all devices."""
        data = await self._post(
            "/battery/replace/read",
            {"otp": self._otp, "acode": self._acode},
        )
        if not data.get("result"):
            return []
        return data.get("msg", {}).get("data", [])

    @property
    def devices(self) -> list[dict]:
        """Return device list from last login."""
        return self._devices
