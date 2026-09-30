"""Terminal presentation: theme, banners, renderers, safe prompts."""

from __future__ import annotations

import sys


class Theme:
    """ANSI colors that degrade to plain text on non-TTY output."""

    def __init__(self, enabled: bool | None = None) -> None:
        use_color = sys.stdout.isatty() if enabled is None else enabled
        codes = {
            "reset": "0", "red": "1;31", "green": "1;32", "yellow": "1;33",
            "blue": "1;34", "magenta": "1;35", "cyan": "1;36", "white": "1;37",
        }
        for name, code in codes.items():
            setattr(self, name, f"\033[{code}m" if use_color else "")

    def c(self, color: str, text: str) -> str:
        return f"{getattr(self, color)}{text}{self.reset}"


MAIN_BANNER = r"""
   ________               __      ______                __
  / ____/ /_  ____  _____/ /_    /_  __/________ ______/ /__
 / / __/ __ \/ __ \/ ___/ __/_____/ / / ___/ __ `/ ___/ //_/
/ /_/ / / / / /_/ (__  ) /_/_____/ / / /  / /_/ / /__/ ,<
\____/_/ /_/\____/____/\__/     /_/ /_/   \__,_/\___/_/|_|
"""

DISCLAIMER = (
    "GhostTrack queries third parties (ipwho.is, ipify.org and public "
    "websites). Use it only for targets you are authorized to investigate; "
    "tracking and username enumeration may be restricted in your jurisdiction."
)


def clear_screen() -> None:
    # ANSI clear + cursor home; works on terminals on all platforms.
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def prompt(label: str) -> str | None:
    """Read one line. Returns None on EOF / Ctrl-D (treat as quit)."""
    try:
        return input(label)
    except EOFError:
        return None


def render_kv(theme: Theme, rows: list[tuple[str, object]]) -> None:
    width = max(len(label) for label, _ in rows)
    for label, value in rows:
        shown = value if value is not None else "N/A"
        print(f" {theme.white}{label.ljust(width)} :{theme.green} {shown}")


def status_text(theme: Theme, status: str) -> str:
    mapping = {
        "FOUND": (theme.green, "[+] FOUND"),
        "NOT_FOUND": (theme.red, "[-] not found"),
        "UNKNOWN": (theme.yellow, "[?] unknown (blocked / anti-bot)"),
    }
    color, text = mapping[status]
    return f"{color}{text}{theme.reset}"
