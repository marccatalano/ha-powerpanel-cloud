"""Constants for PowerPanel Cloud integration."""

DOMAIN = "powerpanel_cloud"
MANUFACTURER = "CyberPower"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60  # seconds

# Device status codes
DEVICE_STATUS = {
    0: "Online",
    1: "Offline",
    2: "Warning",
}

# Battery status codes
BATTERY_STATUS = {
    0: "Normal",
    1: "Low",
    2: "Critical",
}

# Power source codes
POWER_SOURCE = {
    0: "Utility",
    1: "Battery",
    2: "Bypass",
}

# UPS state codes
UPS_STATE = {
    0: "Online",
    1: "On Battery",
    2: "Low Battery",
    3: "Fault",
    4: "Standby",
    5: "ECO",
    6: "Converter",
    7: "Charging",
}

CONF_API_KEY = "api_key"
CONF_AUTH_METHOD = "auth_method"
AUTH_METHOD_API_KEY = "api_key"
AUTH_METHOD_LEGACY = "legacy"

# Official /public/v1 API device status codes (differ from legacy codes above)
DEVICE_STATUS_V2 = {
    0: "Normal",
    1: "Warning",
    2: "Critical",
    3: "Offline",
}

# The only status codes that mean "device unreachable". Every other code
# (Warning/Critical — e.g. running on battery) is a reachable device with an
# active alert, and its entities must stay available so that state is visible.
DEVICE_STATUS_OFFLINE = 1
DEVICE_STATUS_V2_OFFLINE = 3

# Legacy device_status code -> v2 DeviceStatusV2 code. Used when the public API
# returns the legacy-shaped payload (lowercase keys, seen on PRO/MSP accounts in
# issue #1), whose device_status follows the legacy enum. Unknown codes pass
# through unchanged.
LEGACY_TO_V2_DEVICE_STATUS = {
    0: 0,  # Online  -> Normal
    1: 3,  # Offline -> Offline
    2: 1,  # Warning -> Warning
}
