"""Constants for PowerPanel Cloud integration."""

DOMAIN = "powerpanel_cloud"
MANUFACTURER = "CyberPower"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60  # seconds

# Code tables below match the label tables in CyberPower's own PowerPanel Cloud
# web app (powerpanel.cyberpower.com), which reads the same fields from the
# same endpoints as this integration, and the device-status enum in the
# official OpenAPI spec. The legacy device_status field and the public API's
# DeviceStatus share ONE enum (issue #4).

# Device status (legacy "device_status" key). Code 0 keeps its historical
# "Online" label so existing automations don't break.
DEVICE_STATUS = {
    0: "Online",
    1: "Warning",
    2: "Critical",
    3: "Offline",
    4: "Hardware Fault",
}

# The only device status meaning "unreachable". Warning/Critical (e.g. running
# on battery) are reachable devices with an active alert; their entities must
# stay available so that state is visible.
DEVICE_STATUS_OFFLINE = 3

# Battery status ("BatSta") — battery charging state, not charge level.
BATTERY_STATUS = {
    0: "Fully Charged",
    1: "Charging",
    2: "Discharging",
    3: "Testing",
    4: "Not Present",
    5: "Critically Low",
    6: "Normal",
    7: "Not Working",
    8: "Boost Charging",
}

# Power source ("PowSour")
POWER_SOURCE = {
    0: "Utility",
    1: "Battery",
    2: "None",
    3: "Bypass",
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

# Device status for API-key entries ("DeviceStatusV2" key). Same codes as
# DEVICE_STATUS; only the code-0 label differs, preserving each entity's
# existing state string.
DEVICE_STATUS_V2 = {**DEVICE_STATUS, 0: "Normal"}
