# CyberPower PowerPanel Cloud — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/marccatalano/ha-powerpanel-cloud/releases)
[![HA Minimum](https://img.shields.io/badge/HA-2024.1.0+-green.svg)](https://www.home-assistant.io)

A Home Assistant custom integration that pulls live UPS telemetry from [CyberPower PowerPanel Cloud](https://powerpanel.cyberpower.com) into Home Assistant via the cloud API.

Supports all CyberPower UPS units connected to PowerPanel Cloud via the **RCCARD100** or **RCCARD101** network cards.

---

## Features

- **16 sensor entities per UPS device**, including:
  - Battery capacity, voltage, health index, status, and runtime remaining
  - Input/output voltage, frequency, and current
  - Load (watts and percentage)
  - Device status, UPS state, power source, and rated power
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
| UPS State | — | Details |
| Power Source | — | Details |
| Rated Power | VA | Details |

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
