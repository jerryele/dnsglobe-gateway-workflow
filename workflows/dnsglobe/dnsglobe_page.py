import os

from flask import send_from_directory
from main_app import app

from bluecat import route
from bluecat.gateway.decorators import page_exc_handler, require_permission


@route(app, "/dnsglobe/page")
@page_exc_handler(default_message="Failed to load DNSGlobe workflow.")
@require_permission("dnsglobe_page")
def dnsglobe_page():
    return send_from_directory(os.path.dirname(os.path.abspath(str(__file__))), "dnsglobePage/index.html")
