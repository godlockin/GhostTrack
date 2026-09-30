"""Interactive CLI: single while-loop event driver, no recursion."""

from __future__ import annotations

import sys
from pathlib import Path

import phonenumbers

from . import __version__
from .http_client import CachedSession
from .services import (
    FOUND,
    ServiceError,
    lookup_ip,
    lookup_phone,
    probe_username,
    show_my_ip,
)
from .sites import SITES
from .ui import (
    DISCLAIMER,
    MAIN_BANNER,
    Theme,
    clear_screen,
    prompt,
    render_kv,
    status_text,
)

ACCEPT_MARKER = Path.home() / ".ghosttrack" / "disclaimer.accepted"

MENU = """
 [ 1 ] IP address lookup
 [ 2 ] Show my public IP
 [ 3 ] Phone number lookup (offline metadata)
 [ 4 ] Username lookup ({} sites)
 [ 0 ] Exit
""".strip()


def accept_disclaimer(theme: Theme, skip_prompt: bool = False) -> bool:
    if ACCEPT_MARKER.exists():
        return True
    if skip_prompt:
        print(theme.red + DISCLAIMER)
        return False
    print(theme.yellow + DISCLAIMER + theme.reset)
    answer = prompt("Type 'yes' to continue: ")
    if answer is not None and answer.strip().lower() == "yes":
        ACCEPT_MARKER.parent.mkdir(parents=True, exist_ok=True)
        ACCEPT_MARKER.write_text(__version__ + "\n")
        return True
    return False


def action_ip(session: CachedSession, theme: Theme) -> None:
    ip = prompt(f"{theme.white}\nEnter IP target (or 'b' to go back): {theme.green}")
    if ip is None or ip.strip() == "b":
        return
    data = lookup_ip(session, ip)
    lat = data.get("latitude")
    lon = data.get("longitude")
    maps = (
        f"https://www.google.com/maps/@{lat},{lon},12z"
        if lat is not None and lon is not None
        else None
    )
    connection = data.get("connection") or {}
    tz = data.get("timezone") or {}
    flag = data.get("flag") or {}

    render_kv(theme, [
        ("IP target", ip.strip()),
        ("Type", data.get("type")),
        ("Country", data.get("country")),
        ("Country code", data.get("country_code")),
        ("City", data.get("city")),
        ("Continent", data.get("continent")),
        ("Region", data.get("region")),
        ("Latitude", lat),
        ("Longitude", lon),
        ("Maps", maps),
        ("Postal", data.get("postal")),
        ("Calling code", data.get("calling_code")),
        ("Capital", data.get("capital")),
        ("Borders", data.get("borders")),
        ("Flag", flag.get("emoji")),
        ("ASN", connection.get("asn")),
        ("ORG", connection.get("org")),
        ("ISP", connection.get("isp")),
        ("Timezone", tz.get("id")),
        ("UTC offset", tz.get("utc")),
    ])
    print(theme.yellow + "\nLocation is city-level, not an exact address.")


def action_my_ip(session: CachedSession, theme: Theme) -> None:
    print(f"{theme.green}Your public IP: {show_my_ip(session)}")


def action_phone(session: CachedSession, theme: Theme) -> None:
    number = prompt(
        f"{theme.white}\nEnter phone number in E.164, e.g. +8613800138000 "
        f"(or 'b' to go back): {theme.green}"
    )
    if number is None or number.strip() == "b":
        return
    region_answer = prompt(
        f"{theme.white}Default region for numbers without '+' [2-letter code, "
        f"empty = none]: {theme.green}"
    )
    region = region_answer.strip().upper() if region_answer else None

    data = lookup_phone(number, region)
    ptype = data["number_type"]
    type_name = (
        "mobile" if ptype == phonenumbers.PhoneNumberType.MOBILE
        else "fixed-line" if ptype == phonenumbers.PhoneNumberType.FIXED_LINE
        else "other"
    )
    render_kv(theme, [
        ("Location", data["location"]),
        ("Region code", data["region_code"]),
        ("Timezones", ", ".join(data["timezones"])),
        ("Operator", data["operator"]),
        ("Valid", data["valid"]),
        ("Possible", data["possible"]),
        ("International", data["international"]),
        ("Mobile dialing", data["mobile"]),
        ("E.164", data["e164"]),
        ("Country code", data["country_code"]),
        ("Type", type_name),
    ])
    print(theme.yellow + "\nOffline carrier metadata only, not live tracking.")


def action_username(session: CachedSession, theme: Theme) -> None:
    username = prompt(f"{theme.white}\nEnter username (or 'b' to go back): {theme.green}")
    if username is None or username.strip() == "b":
        return

    total = len(SITES)
    done = 0

    def on_result(site_name: str, status: str) -> None:
        nonlocal done
        done += 1
        print(f" [{done}/{total}] {site_name:<14} {status_text(theme, status)}")

    try:
        results = probe_username(session, username, on_result=on_result)
    except KeyboardInterrupt:
        print(theme.yellow + "\nScan interrupted.")
        return

    found = [name for name, st in results.items() if st == FOUND]
    print(f"\n{theme.green}Candidates ({len(found)}): "
          f"{theme.reset}{', '.join(sorted(found)) or 'none'}")
    print(theme.yellow + "Results need manual verification (anti-bot pages, soft-404s).")


def run(accept_disclaimer_flag: bool = False) -> int:
    theme = Theme()
    if not accept_disclaimer(theme, skip_prompt=accept_disclaimer_flag):
        print(theme.red + "Disclaimer not accepted, exiting.")
        return 1

    session = CachedSession()
    try:
        while True:
            clear_screen()
            print(theme.cyan + MAIN_BANNER + theme.reset)
            print(f"{theme.white}GhostTrack v{__version__}{theme.reset}\n")
            print(MENU.format(len(SITES)))
            choice = prompt(f"\n{theme.white}Select option: {theme.reset}")
            if choice is None:
                break
            choice = choice.strip()

            actions = {
                "1": action_ip,
                "2": action_my_ip,
                "3": action_phone,
                "4": action_username,
            }
            action = actions.get(choice)
            if choice == "0":
                break
            if action is None:
                print(theme.red + f"Invalid option: {choice!r}")
            else:
                try:
                    action(session, theme)
                except ServiceError as exc:
                    print(theme.red + str(exc))
                except KeyboardInterrupt:
                    print(theme.yellow + "\nCancelled.")

            if prompt(f"{theme.green}\nPress enter for menu (Ctrl-D to quit): ") is None:
                break
    finally:
        session.close()
        print(theme.reset)
    return 0


def main() -> None:
    sys.exit(run())
