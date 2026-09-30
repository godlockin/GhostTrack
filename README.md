# GhostTrack

OSINT tool for IP address, phone number and username lookups.

<img src="https://github.com/godlockin/GhostTrack/blob/main/asset/bn.png"/>

> ⚠️ **Legal notice**: GhostTrack sends queries to third parties (ipwho.is,
> ipify.org and public websites). Use only against targets you are authorized
> to investigate. Tracking and username enumeration may be restricted in your
> jurisdiction. Results are city-level metadata, not live tracking.

## Install

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
uv run ghosttrack
```

With pip:

```bash
pip install .
ghosttrack
```

For development:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

## Usage

After launch a menu is shown:

```
[ 1 ] IP address lookup        # city/ISP-level info + Google Maps link
[ 2 ] Show my public IP
[ 3 ] Phone number lookup      # offline carrier metadata (phonenumbers)
[ 4 ] Username lookup          # 25 sites, concurrent, with progress
[ 0 ] Exit
```

- Enter `b` at any target prompt to go back to the menu.
- Phone numbers should use E.164 format, e.g. `+8613800138000`; you can set a
  fallback region for numbers without `+`.
- Username results are one of **found** / **not found** / **unknown**
  (anti-bot responses) and should be manually verified.

## Display

`IP lookup`

<img src="https://github.com/godlockin/GhostTrack/blob/main/asset/ip.png"/>

`Phone lookup`

<img src="https://github.com/godlockin/GhostTrack/blob/main/asset/phone.png"/>

`Username lookup`

<img src="https://github.com/godlockin/GhostTrack/blob/main/asset/User.png"/>
