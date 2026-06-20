# Platform Requests

This directory is the formal communication channel between module developers and the platform team.

## How it works

1. **Module developer** — when you need something from the platform that isn't in `modules/sdk/platform_bridge.py`, create a new file in `open/` using the template.
2. **Platform team** — reviews `open/` requests, implements the capability in the SDK, then moves the file to `resolved/` with implementation notes.

## Filing a request

Copy `template.md` to `open/REQ-NNN-short-title.md` (use the next available number).
Fill in all sections. Be specific about what you need and why existing SDK methods don't cover it.

## Request lifecycle

`open/` → (platform team reviews) → `resolved/` (with implementation notes added)
