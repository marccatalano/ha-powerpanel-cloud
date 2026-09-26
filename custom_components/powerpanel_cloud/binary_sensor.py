"""Binary sensor platform for PowerPanel Cloud."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, POWER_SOURCE_BATTERY
from .coordinator import PowerPanelCoordinator
from .entity import PowerPanelEntity, build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    coordinator: PowerPanelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PowerPanelOnBatterySensor(
            coordinator, dcode, build_device_info(dcode, device_data)
        )
        for dcode, device_data in coordinator.data.items()
        # Derived from Power Source; only create it where that field exists.
        if "PowSour" in device_data.get("details", {})
    )


class PowerPanelOnBatterySensor(PowerPanelEntity, BinarySensorEntity):
    """On while the UPS is powering its load from battery.

    No device class: HA's "power" class means on = power detected (the
    inverse), and "battery" means on = battery low — neither fits.
    """

    def __init__(self, coordinator, dcode, device_info) -> None:
        super().__init__(coordinator, dcode, device_info, "on_battery", "On Battery")

    @property
    def is_on(self) -> bool | None:
        source = self._device_data.get("details", {}).get("PowSour")
        if source is None:
            return None
        return source == POWER_SOURCE_BATTERY

    @property
    def icon(self) -> str:
        return "mdi:battery-arrow-down" if self.is_on else "mdi:power-plug-battery"
