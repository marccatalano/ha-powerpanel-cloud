"""Shared entity base for PowerPanel Cloud platforms."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_STATUS_OFFLINE, DOMAIN, MANUFACTURER
from .coordinator import PowerPanelCoordinator


def build_device_info(dcode: str, device_data: dict[str, Any]) -> DeviceInfo:
    """Build the HA device registry entry for one UPS."""
    summary = device_data.get("summary", {})
    details = device_data.get("details", {})
    return DeviceInfo(
        identifiers={(DOMAIN, dcode)},
        name=details.get("DeviceName") or summary.get("device_sn", dcode),
        manufacturer=MANUFACTURER,
        model=details.get("Model") or summary.get("Model", "CyberPower UPS"),
        serial_number=summary.get("device_sn", dcode),
        sw_version=details.get("FV", ""),
    )


class PowerPanelEntity(CoordinatorEntity):
    """Base entity: one UPS, identified by its dcode."""

    def __init__(
        self,
        coordinator: PowerPanelCoordinator,
        dcode: str,
        device_info: DeviceInfo,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._dcode = dcode
        self._attr_device_info = device_info
        self._attr_unique_id = f"{DOMAIN}_{dcode}_{key}"
        self._attr_name = f"{device_info['name']} {name}"

    @property
    def _device_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._dcode, {})

    @property
    def available(self) -> bool:
        summary = self._device_data.get("summary", {})
        # The legacy client stores "device_status", the v2 client
        # "DeviceStatusV2"; both carry the same enum. Only Offline makes the
        # entities unavailable (issue #4).
        status = summary.get("DeviceStatusV2", summary.get("device_status"))
        return (
            super().available
            and self._dcode in self.coordinator.data
            and status != DEVICE_STATUS_OFFLINE
        )
