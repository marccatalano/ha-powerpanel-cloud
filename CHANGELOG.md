# Changelog

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
