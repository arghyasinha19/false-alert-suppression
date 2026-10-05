"""
Custom exceptions for the DNAC client.

Hierarchy:
    DNACError
    ├── DeviceNotFoundError   — no device matched the supplied identifier
    └── DNACConnectionError   — DNAC unreachable, HTTP error, or auth failure
"""


class DNACError(Exception):
    """Base exception for all DNAC client errors."""


class DeviceNotFoundError(DNACError):
    """
    Raised when a DNAC query returns zero matching devices.

    Attributes:
        identifier: The hostname or IP that was searched for.
    """

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"No device found in DNAC matching: {identifier}")


class DNACConnectionError(DNACError):
    """
    Raised when the DNAC API is unreachable, returns an unexpected HTTP
    error (non-401 after retry, 404 on health lookup, 5xx, etc.), or when
    a network-level exception occurs.
    """
