import pytest
from conftest import FakeRawSession, FakeResponse

from ghosttrack.http_client import CachedSession
from ghosttrack.services import (
    FOUND,
    NOT_FOUND,
    UNKNOWN,
    ServiceError,
    lookup_ip,
    lookup_phone,
    probe_site,
    validate_ip,
)
from ghosttrack.sites import Site


def make_session(responses):
    return CachedSession(FakeRawSession(responses), ttl_seconds=60)


def test_validate_ip_v4_and_v6():
    assert validate_ip("8.8.8.8") == "8.8.8.8"
    assert validate_ip(" 2001:db8::1 ") == "2001:db8::1"


def test_validate_ip_rejects_garbage():
    with pytest.raises(ServiceError):
        validate_ip("abc")
    with pytest.raises(ServiceError):
        validate_ip("999.1.1.1")


def test_lookup_ip_success():
    payload = {"success": True, "type": "IPv4", "country": "United States",
               "latitude": 37.33, "longitude": -121.89}
    session = make_session({"https://ipwho.is/8.8.8.8": FakeResponse(json_data=payload)})
    data = lookup_ip(session, "8.8.8.8")
    assert data["country"] == "United States"


def test_lookup_ip_upstream_failure():
    payload = {"success": False, "message": "Invalid IP"}
    session = make_session({"https://ipwho.is/1.1.1.1": FakeResponse(json_data=payload)})
    with pytest.raises(ServiceError, match="Invalid IP"):
        lookup_ip(session, "1.1.1.1")


def test_lookup_ip_bad_json():
    session = make_session({"https://ipwho.is/8.8.8.8": FakeResponse(text="<html>")})
    with pytest.raises(ServiceError):
        lookup_ip(session, "8.8.8.8")


def test_lookup_phone_valid():
    data = lookup_phone("+628123456789", "ID")
    assert data["region_code"] == "ID"
    assert data["valid"] is True
    assert data["e164"] == "+628123456789"


def test_lookup_phone_invalid():
    with pytest.raises(ServiceError):
        lookup_phone("not-a-number", None)


def test_lookup_phone_empty():
    with pytest.raises(ServiceError):
        lookup_phone("   ", "ID")


def test_probe_head_200_is_found():
    site = Site("Example", "https://example.com/{}", head=True)
    session = make_session({"https://example.com/bob": FakeResponse(200)})
    assert probe_site(session, site, "bob") == FOUND


def test_probe_head_404_not_found():
    site = Site("Example", "https://example.com/{}", head=True)
    session = make_session({"https://example.com/bob": FakeResponse(404)})
    assert probe_site(session, site, "bob") == NOT_FOUND


def test_probe_403_is_unknown():
    site = Site("Example", "https://example.com/{}", head=True)
    session = make_session({"https://example.com/bob": FakeResponse(403)})
    assert probe_site(session, site, "bob") == UNKNOWN


def test_probe_body_marker_not_found():
    site = Site("Ex", "https://ex.com/{}",
                not_found_markers=("Sorry, this page isn't available.",))
    body = "<html>Sorry, this page isn't available.</html>"
    session = make_session({
        "https://ex.com/nobody": FakeResponse(200, text=body)
    })
    assert probe_site(session, site, "nobody") == NOT_FOUND
