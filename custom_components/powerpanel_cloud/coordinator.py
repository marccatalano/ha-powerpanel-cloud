"""DataUpdateCoordinator for PowerPanel Cloud."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PowerPanelConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PowerPanelCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from PowerPanel Cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client,  # PowerPanelAPIClient | PowerPanelPublicAPIClient
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
        """Fetch data for all devices via the configured client."""
        try:
            return await self.client.async_fetch_data()
        except PowerPanelConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
