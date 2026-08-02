"""Config flow for PowerPanel Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
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
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=30, max=3600)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate credentials by attempting authentication."""
    session = async_get_clientsession(hass)
    client = PowerPanelAPIClient(data[CONF_EMAIL], data[CONF_PASSWORD], session)
    await client.authenticate()
    devices = client.devices
    return {
        "title": f"PowerPanel Cloud ({data[CONF_EMAIL]})",
        "device_count": len(devices),
    }


class PowerPanelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PowerPanel Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
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
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
