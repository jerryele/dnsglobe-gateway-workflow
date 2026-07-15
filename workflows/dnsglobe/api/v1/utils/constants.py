# Copyright 2026 BlueCat Networks (USA) Inc. and its affiliates. All Rights Reserved.
"""
Constants for the DNSGlobe API.
"""
from typing import Final

# Record types selectable from the UI, same set as dnsglobe's app::RECORD_TYPES.
RECORD_TYPES: Final[list[str]] = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA"]

# A domain label is at most 63 octets, a full name at most 253; this is a
# generous upper bound just to reject obvious garbage before it reaches
# dnspython, not a strict RFC check.
MAX_DOMAIN_LENGTH: Final[int] = 253
