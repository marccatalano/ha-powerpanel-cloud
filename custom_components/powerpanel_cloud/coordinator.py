"""DataUpdateCoordinator for PowerPanel Cloud."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PowerPanelAPIClient, PowerPanelConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PowerPanelCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from PowerPanel Cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PowerPanelAPIClient,
        scan_interval: int,
    ) -> None:
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data for all devices."""
        try:
            # Get summary status for all devices in one call
            statuses = await self.client.get_device_status()
        except PowerPanelConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        if not statuses:
            raise UpdateFailed("No device status returned")

        result = {}
        for device in statuses:
            dcode = str(device.get("dcode", ""))
            if not dcode:
                continue

            # Get detailed telemetry for each device
            try:
                details = await self.client.get_device_details(dcode)
            except PowerPanelConnectionError as err:
                _LOGGER.warning("Failed to get details for device %s: %s", dcode, err)
                details = None

            result[dcode] = {
                "summary": device,
                "details": details or {},
            }

        return result
