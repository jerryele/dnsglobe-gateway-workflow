"""
Built-in public DNS resolver list, ported from the dnsglobe TUI project's
src/resolvers.rs (https://github.com/514-labs/dnsglobe).

Anycast networks are marked as such in `location` - the answering node is the
one nearest the Gateway host, not necessarily where `lat`/`lon` points. Coords
are only used to place the dot on the world map.
"""
from typing import Final, Optional, TypedDict


class Resolver(TypedDict):
    name: str
    location: str
    ip: str
    # None for a custom-imported resolver with no map position given.
    lat: Optional[float]
    lon: Optional[float]


# Same 34 resolvers as dnsglobe's BUILTIN list, same grouping/order.
RESOLVERS: Final[list[Resolver]] = [
    # Global anycast
    {"name": "Google Public DNS", "location": "Anycast", "ip": "8.8.8.8", "lat": 37.4, "lon": -122.1},
    {"name": "Cloudflare", "location": "Anycast", "ip": "1.1.1.1", "lat": 37.8, "lon": -122.4},
    {"name": "Quad9", "location": "CH/Any", "ip": "9.9.9.9", "lat": 47.4, "lon": 8.5},
    {"name": "OpenDNS (Cisco)", "location": "US/Any", "ip": "208.67.222.222", "lat": 33.9, "lon": -118.2},
    {"name": "CleanBrowsing", "location": "Anycast", "ip": "185.228.168.9", "lat": 33.4, "lon": -112.0},
    # North America
    {"name": "Level3", "location": "US", "ip": "4.2.2.2", "lat": 39.7, "lon": -105.0},
    {"name": "Lumen (Qwest)", "location": "US", "ip": "205.171.3.66", "lat": 40.4, "lon": -104.0},
    {"name": "Hurricane Electric", "location": "US", "ip": "74.82.42.42", "lat": 37.6, "lon": -122.0},
    {"name": "Neustar UltraDNS", "location": "US/Any", "ip": "64.6.64.6", "lat": 39.0, "lon": -77.5},
    {"name": "Comodo Secure DNS", "location": "US", "ip": "8.26.56.26", "lat": 40.9, "lon": -74.2},
    {"name": "FortiGuard", "location": "US/Any", "ip": "208.91.112.53", "lat": 37.3, "lon": -121.9},
    {"name": "CIRA Canadian Shield", "location": "CA", "ip": "149.112.121.10", "lat": 45.4, "lon": -75.7},
    {"name": "ControlD", "location": "CA/Any", "ip": "76.76.2.0", "lat": 43.7, "lon": -79.4},
    # Europe
    {"name": "DNS4EU", "location": "EU/Any", "ip": "86.54.11.100", "lat": 50.1, "lon": 14.4},
    {"name": "CZ.NIC ODVR", "location": "CZ", "ip": "193.17.47.1", "lat": 49.9, "lon": 15.3},
    {"name": "AdGuard DNS", "location": "EU/Any", "ip": "94.140.14.14", "lat": 34.7, "lon": 33.0},
    {"name": "Gcore DNS", "location": "LU/Any", "ip": "95.85.95.85", "lat": 49.6, "lon": 6.1},
    {"name": "DNS.SB", "location": "DE/Any", "ip": "185.222.222.222", "lat": 50.1, "lon": 8.7},
    # Russia / Middle East
    {"name": "SafeDNS", "location": "RU", "ip": "195.46.39.39", "lat": 55.8, "lon": 37.6},
    {"name": "Yandex DNS", "location": "RU", "ip": "77.88.8.8", "lat": 55.6, "lon": 37.9},
    {"name": "Comss.one", "location": "RU", "ip": "83.220.169.155", "lat": 56.3, "lon": 38.1},
    {"name": "Bezeq Intl", "location": "IL", "ip": "192.115.106.10", "lat": 32.1, "lon": 34.8},
    # East Asia
    {"name": "114DNS", "location": "CN", "ip": "114.114.114.114", "lat": 32.1, "lon": 118.8},
    {"name": "AliDNS", "location": "CN", "ip": "223.5.5.5", "lat": 30.3, "lon": 120.2},
    {"name": "DNSPod (Tencent)", "location": "CN", "ip": "119.29.29.29", "lat": 22.5, "lon": 114.1},
    {"name": "Baidu DNS", "location": "CN", "ip": "180.76.76.76", "lat": 39.9, "lon": 116.4},
    {"name": "CNNIC sDNS", "location": "CN", "ip": "1.2.4.8", "lat": 40.5, "lon": 116.9},
    {"name": "360 Secure DNS", "location": "CN", "ip": "101.226.4.6", "lat": 31.2, "lon": 121.5},
    {"name": "KT (Kornet)", "location": "KR", "ip": "168.126.63.1", "lat": 37.6, "lon": 127.0},
    {"name": "LG U+", "location": "KR", "ip": "164.124.101.2", "lat": 36.5, "lon": 127.9},
    {"name": "HiNet (Chunghwa)", "location": "TW", "ip": "168.95.1.1", "lat": 25.0, "lon": 121.6},
    # Southern hemisphere
    {"name": "Telstra", "location": "AU", "ip": "139.130.4.4", "lat": -33.9, "lon": 151.2},
    {"name": "SafeSurfer", "location": "NZ", "ip": "104.197.28.121", "lat": -36.8, "lon": 174.8},
    {"name": "UOL", "location": "BR", "ip": "200.221.11.100", "lat": -23.5, "lon": -46.6},
]
