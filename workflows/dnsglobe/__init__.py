# Copyright 2026 BlueCat Networks (USA) Inc. and its affiliates. All Rights Reserved.
"""
DNSGlobe workflow initialization.

Single workflow package providing both the navigable UI page (via `sub_pages`,
type="ui") and the flask_restx REST API that page's JavaScript calls to run
DNS propagation checks against 34 public resolvers worldwide. Ported from the
dnsglobe TUI project (https://github.com/514-labs/dnsglobe) - same resolver
list and answer-grouping logic, reworked as a Gateway web workflow instead of
a terminal UI.
"""
from typing import Final

from flask import Blueprint
from flask_restx import Api
from main_app import app

# Define workflow metadata
type: str = "ui"  # noqa: A001
sub_pages: list[dict[str, str]] = [
    {
        "name": "dnsglobe_page",
        "title": "DNSGlobe",
        "endpoint": "dnsglobe/page",
        "description": "Check DNS record propagation across public resolvers worldwide",
    },
]

API_VERSION: Final[str] = "1.0"
API_PREFIX: Final[str] = "/dnsglobe/v1"

api_endpoints: Blueprint = Blueprint(
    "dnsglobe_api",  # Blueprint name
    "dnsglobe_api",  # Import name
)

dnsglobe_api: Api = Api(
    api_endpoints,
    version=API_VERSION,
    title="DNSGlobe API",
    description="REST API for checking DNS propagation across public resolvers worldwide",
    doc="/doc",
    default_label="DNSGlobe",
    validate=True,
)

# Register API blueprint with Flask app
app.register_blueprint(api_endpoints, url_prefix=API_PREFIX)

# Register API namespaces. The "propagation" namespace's routes end up at
# API_PREFIX + "/propagation/resolvers" and API_PREFIX + "/propagation/check".
from .api import v1

for namespace in v1.namespaces:
    dnsglobe_api.add_namespace(namespace)
