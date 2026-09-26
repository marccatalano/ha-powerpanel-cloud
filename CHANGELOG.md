# Changelog

## [1.3.1] - 2026-09-26

### Fixed
- `brand/icon@2x.png` is now a true 512×512 hDPI icon (was a 256×256
  duplicate), rendered from the vector wordmark. Sharper logo in Home
  Assistant on high-DPI displays.

### Note
- The HACS store may still show "icon not available". This is a HACS
  frontend limitation (hacs/integration#5223): HACS still loads icons from
  the legacy brands CDN rather than the in-integration `brand/` folder
  supported since HA 2026.3. The icon displays correctly in Settings →
  Devices & Services.

## [1.3.0] - 2026-09-26

### Added
- **On Battery** binary sensor per UPS: on while the load is running from
  battery (Power Source = Battery). The simplest trigger for outage
  automations. (#6)
- **Input Status** sensor (Normal, Power Anomaly, Under Voltage, Over Voltage,
  Frequency Failure, Generator). Reads Power Anomaly during a utility failure
  and also reports brownouts and over-voltage. (#6)
- **Output Status** sensor (Normal, Overload, Voltage Buck/Boost, Bypass
  modes, Eco Mode, No Output, Output Short Circuit, and others).
- API-key entries now receive input and output status as well.

### Deprecated
- **UPS State**: its source field is not defined by CyberPower and can read
  Online while on battery. Existing entities keep working; new installs get it
  disabled by default. Use On Battery, Power Source or Input Status instead.
  It will be removed in a future major release. (#6)

### Fixed
- Status sensors no longer error if a 3-phase UPS reports a list of codes; the
  raw value is shown instead.

## [1.2.1] - 2026-09-24

### Fixed
- Entities no longer go unavailable while a UPS is on battery or has any other
  active alert. The device-status table was wrong since 1.0.0: code 1 is
  Warning (e.g. utility power failure), not Offline, and availability required
  status 0. Only Offline (code 3) now makes entities unavailable. (#4)
- Device Status, Battery Status and Power Source now use CyberPower's own code
  tables. The legacy and public APIs share one device-status enum.

### Changed
- Battery Status labels changed to CyberPower's charging-state values (Fully
  Charged, Charging, Discharging, Testing, Not Present, Critically Low, Normal,
  Not Working, Boost Charging). The previous "Normal/Low/Critical" labels were
  incorrect; code 0 was "Normal" and is now "Fully Charged". Update any
  automations that match on Battery Status text.
- Device Status gains Critical, Offline and Hardware Fault; Power Source code 2
  is now "None" and 3 "Bypass".

### Added
- Debug logging of each poll's raw summary/details per device.

## [1.0.0] - 2026-05-02

### Added
- Initial release
- Full config flow UI (no YAML required)
- Auto-discovery of all UPS devices on the PowerPanel Cloud account
- 16 sensor entities per device: battery, voltage, frequency, load, runtime, status
- Automatic token refresh on expiry
- Configurable poll interval (default: 60 seconds)
- Support for RCCARD100 / RCCARD101 network cards
