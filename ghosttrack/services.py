"""Pure business logic: no input()/print(), data returned as plain structures.

Status conventions:
  * lookup functions return ``{"ok": bool, ...}``.
  * username probes return one of ``FOUND`` / ``NOT_FOUND`` / ``UNKNOWN``.
"""

from __future__ import annotations

import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import phonenumbers
import requests
from phonenumbers import carrier, geocoder, timezone

from .http_client import CachedSession
from .sites import SITES, Site

FOUND = "FOUND"
NOT_FOUND = "NOT_FOUND"
UNKNOWN = "UNKNOWN"


class ServiceError(Exception):
    """Expected, user-facing lookup failure (bad input, network, upstream)."""


def validate_ip(ip: str) -> str:
    """Return normalized IP, or raise ServiceError. Accepts v4/v6 only."""
    try:
        return str(ipaddress.ip_address(ip.strip()))
    except ValueError as exc:
        raise ServiceError(f"Invalid IP address: {ip!r}") from exc


def lookup_ip(session: CachedSession, ip: str) -> dict[str, object]:
    """Fetch ipwho.is data. Returns the parsed JSON dict on success."""
    normalized = validate_ip(ip)
    try:
        response = session.get(f"https://ipwho.is/{normalized}")
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ServiceError(f"IP lookup failed: {exc}") from exc

    if not data.get("success", True):
        raise ServiceError(data.get("message", "IP lookup returned no result"))
    return data


def show_my_ip(session: CachedSession) -> str:
    try:
        return session.get("https://api.ipify.org/", use_cache=False).text
    except requests.RequestException as exc:
        raise ServiceError(f"Cannot reach ipify: {exc}") from exc


def lookup_phone(number: str, region: str, lang: str = "en") -> dict[str, object]:
    """Offline phone metadata via phonenumbers."""
    raw = number.strip()
    if not raw:
        raise ServiceError("Empty phone number")
    try:
        parsed = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException as exc:
        raise ServiceError(f"Invalid phone number: {exc}") from exc

    return {
        "location": geocoder.description_for_number(parsed, lang) or None,
        "region_code": phonenumbers.region_code_for_number(parsed),
        "timezones": timezone.time_zones_for_number(parsed),
        "operator": carrier.name_for_number(parsed, "en") or None,
        "valid": phonenumbers.is_valid_number(parsed),
        "possible": phonenumbers.is_possible_number(parsed),
        "international": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        "mobile": phonenumbers.format_number_for_mobile_dialing(
            parsed, region or "US", with_formatting=True
        ),
        "national": parsed.national_number,
        "e164": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        ),
        "country_code": parsed.country_code,
        "number_type": phonenumbers.number_type(parsed),
    }


def _classify_response(site: Site, status: int, text: str) -> str:
    if status == 404:
        return NOT_FOUND
    if status in (403, 429, 999):
        return UNKNOWN
    if status >= 400:
        return UNKNOWN
    if site.not_found_markers:
        head = text[:200_000]
        if any(marker in head for marker in site.not_found_markers):
            return NOT_FOUND
    return FOUND


def probe_site(session: CachedSession, site: Site, username: str) -> str:
    url = site.url.format(username)
    try:
        if site.head:
            try:
                response = session.head(url)
                if response.status_code not in (403, 405, 429, 999):
                    return _classify_response(site, response.status_code, "")
            except requests.RequestException:
                pass  # fall back to GET
        response = session.get(url)
        return _classify_response(site, response.status_code, response.text)
    except requests.RequestException:
        return UNKNOWN


def probe_username(
    session: CachedSession,
    username: str,
    *,
    max_workers: int = 10,
    on_result: Callable[[str, str], None] | None = None,
) -> dict[str, str]:
    """Probe all sites concurrently. Returns {site name: status}."""
    name = username.strip()
    if not name:
        raise ServiceError("Empty username")

    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(probe_site, session, site, name): site.name
            for site in SITES
        }
        for future in as_completed(futures):
            site_name = futures[future]
            results[site_name] = future.result()
            if on_result:
                on_result(site_name, results[site_name])
    return results
