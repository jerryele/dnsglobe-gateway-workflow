# Copyright 2026 BlueCat Networks (USA) Inc. and its affiliates. All Rights Reserved.
"""
Persisted custom resolver list (the "import your own NS servers" feature).

Stored under `/bluecat_gateway`, the Gateway's persistent data mount (backed
by the host's gwdata directory), rather than inside this workflow's own code
directory - a redeploy replaces `workflows/dnsglobe` wholesale, which would
otherwise wipe a user's imported list along with every code update. Absent
file = the built-in list from `resolvers.py` is active.
"""
import json
import os
from typing import Final

from .resolvers import RESOLVERS as DEFAULT_RESOLVERS
from .resolvers import Resolver

STORE_DIR: Final[str] = "/bluecat_gateway/dnsglobe_data"
STORE_PATH: Final[str] = STORE_DIR + "/resolvers.json"


def is_custom() -> bool:
    return os.path.isfile(STORE_PATH)


def get_active() -> list[Resolver]:
    """The resolver list to query with: the persisted custom list if one
    exists and is readable, otherwise the built-in defaults. An empty list is
    a legitimate custom state (the "delete all" action) and is returned as-is
    - it must NOT fall back to the defaults, or delete-all would silently
    undo itself on the next load."""
    if os.path.isfile(STORE_PATH):
        try:
            with open(STORE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (OSError, ValueError):
            pass  # corrupt or unreadable - fall back to defaults rather than error
    return DEFAULT_RESOLVERS


def set_custom(resolvers: list[Resolver]) -> None:
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(resolvers, f, indent=2)
        f.write("\n")


def reset() -> None:
    if os.path.isfile(STORE_PATH):
        os.remove(STORE_PATH)
