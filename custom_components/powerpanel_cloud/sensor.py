"""Sensor platform for PowerPanel Cloud."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BATTERY_STATUS,
    DEVICE_STATUS,
    DEVICE_STATUS_V2,
    DOMAIN,
    MANUFACTURER,
    POWER_SOURCE,
    UPS_STATE,
)
from .coordinator import PowerPanelCoordinator


@dataclass
class PowerPanelSensorDescription(SensorEntityDescription):
    """Describe a PowerPanel sensor."""

    source: str = "details"  # "details" or "summary"
    value_map: dict | None = None


SENSOR_DESCRIPTIONS: tuple[PowerPanelSensorDescription, ...] = (
    # ── From details endpoint ──────────────────────────────────────────────────
    PowerPanelSensorDescription(
        key="InVolt",
        name="Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="OutVolt",
        name="Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="BatVolt",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="InFreq",
        name="Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="OutFreq",
        name="Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="OutCur",
        name="Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="LoadPct",
        name="Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        source="details",
    ),
    PowerPanelSensorDescription(
        key="Load",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
    PowerPanelSensorDescription(
        key="BHI",
        name="Battery Health Index",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-variant",
        source="details",
    ),
    PowerPanelSensorDescription(
        key="upsState",
        name="UPS State",
        source="details",
        icon="mdi:power-plug",
        value_map=UPS_STATE,
    ),
    PowerPanelSensorDescription(
        key="PowSour",
        name="Power Source",
        source="details",
        icon="mdi:transmission-tower",
        value_map=POWER_SOURCE,
    ),
    PowerPanelSensorDescription(
        key="RatPow",
        name="Rated Power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        source="details",
    ),
    # ── From summary endpoint ──────────────────────────────────────────────────
    PowerPanelSensorDescription(
        key="BatCap",
        name="Battery Capacity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        source="summary",
    ),
    PowerPanelSensorDescription(
        key="BatRun",
        name="Runtime Remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        source="summary",
    ),
    PowerPanelSensorDescription(
        key="BatSta",
        name="Battery Status",
        source="summary",
        icon="mdi:battery",
        value_map=BATTERY_STATUS,
    ),
    PowerPanelSensorDescription(
        key="device_status",
        name="Device Status",
        source="summary",
        icon="mdi:power",
        value_map=DEVICE_STATUS,
    ),
    # ── Official /public/v1 API (v2 client) ───────────────────────────────────
    # The v2 status enum differs from the legacy one, so it lives under its
    # own key/map instead of being coerced into the legacy codes.
    PowerPanelSensorDescription(
        key="DeviceStatusV2",
        name="Device Status",
        source="summary",
        icon="mdi:power",
        value_map=DEVICE_STATUS_V2,
    ),
    PowerPanelSensorDescription(
        key="UpsTemperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        source="details",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: PowerPanelCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for dcode, device_data in coordinator.data.items():
        summary = device_data.get("summary", {})
        details = device_data.get("details", {})

        device_name = details.get("DeviceName") or summary.get("device_sn", dcode)
        model = details.get("Model") or summary.get("Model", "CyberPower UPS")
        serial = summary.get("device_sn", dcode)
        firmware = details.get("FV", "")

        device_info = DeviceInfo(
            identifiers={(DOMAIN, dcode)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=model,
            serial_number=serial,
            sw_version=firmware,
        )

        for description in SENSOR_DESCRIPTIONS:
            # Only create sensor if the key exists in the data source
            source_data = details if description.source == "details" else summary
            if description.key not in source_data:
                continue

            entities.append(
                PowerPanelSensor(
                    coordinator=coordinator,
                    description=description,
                    dcode=dcode,
                    device_info=device_info,
                )
            )

    async_add_entities(entities)


class PowerPanelSensor(CoordinatorEntity, SensorEntity):
    """A sensor for a PowerPanel Cloud UPS device."""

    entity_description: PowerPanelSensorDescription

    def __init__(
        self,
        coordinator: PowerPanelCoordinator,
        description: PowerPanelSensorDescription,
        dcode: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._dcode = dcode
        self._attr_device_info = device_info
        self._attr_unique_id = f"{DOMAIN}_{dcode}_{description.key}"
        self._attr_name = f"{device_info['name']} {description.name}"

    @property
    def _device_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._dcode, {})

    @property
    def native_value(self) -> Any:
        source = self.entity_description.source
        data = self._device_data.get(source, {})
        raw = data.get(self.entity_description.key)

        if raw is None:
            return None

        value_map = self.entity_description.value_map
        if value_map is not None:
            return value_map.get(raw, raw)

        return raw

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._dcode in self.coordinator.data
            and self._device_data.get("summary", {}).get("device_status") == 0
        )
