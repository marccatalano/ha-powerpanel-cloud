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
