"""Config flow for PowerPanel Cloud integration."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    PowerPanelAPIClient,
    PowerPanelAuthError,
    PowerPanelConnectionError,
    PowerPanelTwoFactorError,
)
from .api_v2 import PowerPanelPublicAPIClient
from .const import (
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SELECTOR = vol.All(int, vol.Range(min=30, max=3600))

STEP_API_KEY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
    }
)

STEP_LEGACY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
    }
)


async def _validate_api_key(hass: HomeAssistant, api_key: str) -> dict[str, Any]:
    """Validate an API key against the official /public/v1 API."""
    session = async_get_clientsession(hass)
    client = PowerPanelPublicAPIClient(api_key, session)
    await client.authenticate()
    return {
        "title": "PowerPanel Cloud (API key)",
        "is_pro": client.is_pro,
    }


async def _validate_legacy(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate email/password against the legacy API."""
    session = async_get_clientsession(hass)
    client = PowerPanelAPIClient(data[CONF_EMAIL], data[CONF_PASSWORD], session)
    await client.authenticate()
    return {
        "title": f"PowerPanel Cloud ({data[CONF_EMAIL]})",
        "device_count": len(client.devices),
    }


class PowerPanelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PowerPanel Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Let the user pick an authentication method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["api_key", "legacy"],
        )

    async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Official public API: API key (recommended)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_api_key(self.hass, user_input[CONF_API_KEY])
            except PowerPanelAuthError:
                errors["base"] = "invalid_api_key"
            except PowerPanelConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during API key setup")
                errors["base"] = "unknown"
            else:
                key_digest = hashlib.sha256(
                    user_input[CONF_API_KEY].strip().encode()
                ).hexdigest()[:12]
                await self.async_set_unique_id(f"apikey_{key_digest}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="api_key",
            data_schema=STEP_API_KEY_SCHEMA,
            errors=errors,
        )

    async def async_step_legacy(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Legacy reverse-engineered API: email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_legacy(self.hass, user_input)
            except PowerPanelTwoFactorError:
                errors["base"] = "two_factor_unsupported"
            except PowerPanelAuthError:
                errors["base"] = "invalid_auth"
            except PowerPanelConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="legacy",
            data_schema=STEP_LEGACY_SCHEMA,
            errors=errors,
        )
