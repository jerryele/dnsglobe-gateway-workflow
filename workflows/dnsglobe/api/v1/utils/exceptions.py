"""
Custom exceptions for the DNSGlobe API.
"""


class InvalidCheckRequest(Exception):
    """Raised when a /check request has a missing or malformed domain/record type."""
