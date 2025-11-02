DOMAIN = "audac_mtx"
DEFAULT_PORT = 5001
DEFAULT_HOST = "192.168.1.100"
DEFAULT_ZONES = 4  # MTX48
DEFAULT_DEVICE_ID = "M001"  # destination (matrix)
DEFAULT_SOURCE_ID = "F001"  # source (control panel)

TIMEOUT = 3.0
RECV_EOL = b"\r\n"
SEND_EOL = "\r\n"

# Rate limit minimal entre deux commandes (ms)
DEFAULT_RATE_LIMIT_MS = 120
DEFAULT_POLL_INTERVAL = 5  # s

# Index -> Friendly name
SUPPORTED_SOURCES = {
    1: "Mic 1",
    2: "Mic 2",
    3: "Line 3",
    4: "Line 4",
    5: "Line 5",
    6: "Line 6",
    7: "WLI/MWX65",
    8: "WMI",
}

# Inverse pour les sélections par nom
FRIENDLY_TO_INDEX = {v: k for k, v in SUPPORTED_SOURCES.items()}
