# Changelog

## [1.2.1] - 2026-09-23

### Fixed
- Entities no longer go unavailable while a UPS is on battery or has any other
  active alert. Availability previously required device status to be exactly
  Online/Normal, so Warning/Critical states (including utility power failure)
  hid every entity and Power Source / UPS State never showed Battery. Now only
  an Offline device is treated as unavailable. (#4)
- API-key entries on accounts that return the legacy-shaped status payload now
  translate its legacy status codes into the v2 enum, so the Device Status
  sensor shows the correct label (Offline was shown as Warning, Warning as
  Critical).

## [1.0.0] - 2026-05-02

### Added
- Initial release
- Full config flow UI (no YAML required)
- Auto-discovery of all UPS devices on the PowerPanel Cloud account
- 16 sensor entities per device: battery, voltage, frequency, load, runtime, status
- Automatic token refresh on expiry
- Configurable poll interval (default: 60 seconds)
- Support for RCCARD100 / RCCARD101 network cards
