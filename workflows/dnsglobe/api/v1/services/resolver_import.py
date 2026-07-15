"""
Bulk-import parser for user-supplied resolver lists (.txt or .csv). One lenient
parser handles both: fields split on comma if the line has one, else on
whitespace; column order is ip[,name[,location[,lat[,lon]]]] unless the first
data line is a header naming columns explicitly (must include "ip").

Deliberately forgiving - a malformed line is skipped with a reported reason
rather than failing the whole import, so one typo in a 40-line paste doesn't
lose the other 39.
"""
import ipaddress
from typing import Final

from .resolvers import Resolver

MAX_RESOLVERS: Final[int] = 200
DEFAULT_COLUMNS: Final[list] = ["ip", "name", "location", "lat", "lon"]


def _split_fields(line: str) -> list:
    if "," in line:
        return [f.strip() for f in line.split(",")]
    return line.split()


def _looks_like_header(fields: list) -> bool:
    return "ip" in [f.strip().lower() for f in fields]


def parse(text: str) -> tuple:
    """Return (valid Resolver list, list of human-readable per-line problems)."""
    resolvers: list = []
    errors: list = []
    seen_ips: set = set()
    columns = DEFAULT_COLUMNS
    header_checked = False

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        fields = _split_fields(line)

        if not header_checked:
            header_checked = True
            if _looks_like_header(fields):
                columns = [f.strip().lower() for f in fields]
                continue

        row = dict(zip(columns, fields))

        ip = row.get("ip", "").strip()
        if not ip:
            errors.append(f"line {lineno}: missing IP address, skipped")
            continue
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            errors.append(f"line {lineno}: invalid IP address {ip!r}, skipped")
            continue
        if ip in seen_ips:
            errors.append(f"line {lineno}: duplicate IP {ip}, skipped")
            continue

        name = row.get("name", "").strip() or ip
        location = row.get("location", "").strip()
        lat_raw = row.get("lat", "").strip()
        lon_raw = row.get("lon", "").strip()
        lat = lon = None
        if lat_raw and lon_raw:
            try:
                lat, lon = float(lat_raw), float(lon_raw)
            except ValueError:
                errors.append(f"line {lineno}: invalid lat/lon, importing {ip} without a map position")
        elif lat_raw or lon_raw:
            errors.append(f"line {lineno}: lat and lon must both be given, importing {ip} without a map position")

        seen_ips.add(ip)
        resolvers.append({"name": name, "location": location, "ip": ip, "lat": lat, "lon": lon})

        if len(resolvers) >= MAX_RESOLVERS:
            errors.append(f"stopped at {MAX_RESOLVERS} resolvers - the rest of the file was not read")
            break

    return resolvers, errors


def validate_manual_entry(name, ip, location, lat_raw, lon_raw) -> tuple:
    """Validate one resolver's fields from the manual add-resolver form. Same
    rules as the bulk-import parser's per-line validation. Returns
    (Resolver, None) on success or (None, error message) on failure."""
    ip = (ip or "").strip()
    if not ip:
        return None, "IP address is required"
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None, f"invalid IP address {ip!r}"

    name = (name or "").strip() or ip
    location = (location or "").strip()
    lat_raw = str(lat_raw or "").strip()
    lon_raw = str(lon_raw or "").strip()
    lat = lon = None
    if lat_raw and lon_raw:
        try:
            lat, lon = float(lat_raw), float(lon_raw)
        except ValueError:
            return None, "lat/lon must be numbers"
    elif lat_raw or lon_raw:
        return None, "lat and lon must both be given, or both left blank"

    return {"name": name, "location": location, "ip": ip, "lat": lat, "lon": lon}, None
