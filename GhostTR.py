#!/usr/bin/env python3
"""Backward-compatible entry point. Prefer the installed `ghosttrack` command."""

from ghosttrack.cli import run

if __name__ == "__main__":
    raise SystemExit(run())
