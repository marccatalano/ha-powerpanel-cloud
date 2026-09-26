# CyberPower PowerPanel Cloud — Home Assistant Integration

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/marccatalano/ha-powerpanel-cloud)](https://github.com/marccatalano/ha-powerpanel-cloud/releases/latest)
[![HA Minimum](https://img.shields.io/badge/HA-2024.1.0+-green.svg)](https://www.home-assistant.io)

A Home Assistant custom integration that pulls live UPS telemetry from [CyberPower PowerPanel Cloud](https://powerpanel.cyberpower.com) into Home Assistant via the cloud API.

Supports all CyberPower UPS units connected to PowerPanel Cloud via the **RCCARD100** or **RCCARD101** network cards.

---

## Features

- **Up to 18 sensor entities and an On Battery binary sensor per UPS device**, including:
  - Battery capacity, voltage, health index, status, and runtime remaining
  - Input/output voltage, frequency, and current
  - Load (watts and percentage)
  - Device status, power source, input/output status, and rated power
- **Multi-device support** — all UPS units on your account are discovered automatically
- Configurable **poll interval** (default: 60 seconds)
- Automatic **token refresh** on expiry
- Full **config flow UI** — no YAML required

---

## Prerequisites

- A CyberPower UPS with an **RCCARD100** or **RCCARD101** network management card installed
- An active [PowerPanel Cloud](https://powerpanel.cyberpower.com) account with your device(s) registered
- Home Assistant 2024.1.0 or later

> **Note:** The RCCARD100 free tier covers a single device. Multiple devices require a paid PowerPanel Cloud subscription.

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/marccatalano/ha-powerpanel-cloud` as an **Integration**
4. Search for **CyberPower PowerPanel Cloud** and install
5. Restart Home Assistant

### Manual

1. Download the latest release zip from [Releases](https://github.com/marccatalano/ha-powerpanel-cloud/releases)
2. Extract and copy the `custom_components/powerpanel_cloud/` folder to your HA `config/custom_components/` directory
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **CyberPower PowerPanel Cloud**
3. Enter your PowerPanel Cloud **email address** and **password**
4. Optionally adjust the **poll interval** (default: 60 seconds)
5. Click **Submit**

All UPS devices on your account will be discovered and created automatically as HA devices.

### Choosing a poll interval

The RCCARD uploads to PowerPanel Cloud roughly every 5 minutes on mains power. On a power event it uploads immediately, then about once a minute until power is restored. The default 60-second poll therefore catches outages and restores within about a minute; polling faster than 60 seconds gains nothing, and longer intervals delay outage detection by up to the interval.

While a UPS is on battery, **Power Source** reads `Battery` and **Device Status** reads `Warning`; these are the reliable on-battery signals. **On Battery** turns on at the same moment. (**UPS State** is deprecated and can stay `Online` during an outage.)

Use **On Battery** or **Power Source** to trigger outage and power-restored automations, not **Battery Status**. The card can report `Discharging` for one more upload after mains returns, while everything else already reads normal.

---

## Sensors

Each UPS device exposes the following entities:

| Sensor | Unit | Source |
|---|---|---|
| Battery Capacity | % | Summary |
| Battery Status | — | Summary |
| Battery Voltage | V | Details |
| Battery Health Index | % | Details |
| Runtime Remaining | min | Summary |
| Device Status | — | Summary |
| Input Voltage | V | Details |
| Output Voltage | V | Details |
| Input Frequency | Hz | Details |
| Output Frequency | Hz | Details |
| Output Current | A | Details |
| Load | % | Details |
| Load Power | W | Details |
| Power Source | — | Details |
| Input Status | — | Details |
| Output Status | — | Details |
| Rated Power | VA | Details |
| UPS State *(deprecated, disabled by default)* | — | Details |

It also exposes an **On Battery** binary sensor, which is on while the UPS is running its load from battery.

Status values use CyberPower's own labels. **Input Status** is `Normal` on healthy mains and `Power Anomaly` during an outage; it also reports `Under Voltage`, `Over Voltage`, `Frequency Failure` and `Generator`. **Output Status** is `Normal` in regular operation and reports conditions such as `Overload`, `Bypass`, `Eco Mode` and `No Output`. It stays `Normal` on battery, because the UPS is still delivering normal output.

Labels follow CyberPower's PowerPanel Cloud web app. The PowerPanel mobile app words some codes differently; for example, it shows Input Status code 0 as "Power outage" rather than "Power Anomaly".

**UPS State is deprecated.** CyberPower doesn't define the field it reads, and it can stay `Online` during an outage. Existing installs keep the entity; new installs have it disabled. Use **On Battery**, **Power Source** or **Input Status** instead.

Entities are only created for fields your UPS reports, so some models or account types show fewer. 3-phase UPS models report input and output status per phase; these are shown as raw values.

---

## Disclaimer

This integration uses an unofficial, reverse-engineered API. It is not affiliated with or endorsed by CyberPower Systems. CyberPower may change their API at any time, which could break this integration. Use at your own risk.

If CyberPower ever releases an official API or Home Assistant integration, that should be preferred.

---

## Contributing

Pull requests welcome. Please open an issue first to discuss any significant changes.

---

## License

MIT License — see [LICENSE](LICENSE)
