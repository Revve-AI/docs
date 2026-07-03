#!/usr/bin/env python3
"""Allowlist conformance check for the api-reference skill.

The one rule that skill exists to protect: no endpoint appears in the public
OpenAPI spec unless a human approved it. This is the mechanical backstop.

Reads (repo root):
  api-reference/openapi.json          — the public spec
  .api-reference-allowlist.json       — {"approved": [...], "rejected": [...]}
    entries may be "METHOD /path" strings or objects with an "endpoint" key.

Prints three lists; exits 1 if the spec contains anything not approved or
anything rejected, else 0. Exits 0 with a note if the spec doesn't exist yet.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "api-reference" / "openapi.json"
ALLOWLIST = ROOT / ".api-reference-allowlist.json"

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def norm(entry):
    if isinstance(entry, dict):
        entry = entry.get("endpoint", "")
    parts = entry.split(None, 1)
    if len(parts) == 2:
        return f"{parts[0].upper()} {parts[1].strip()}"
    return entry.strip()


def main():
    if not SPEC.exists():
        print("OK: no api-reference/openapi.json yet — nothing to check")
        return 0

    spec = json.loads(SPEC.read_text())
    spec_endpoints = set()
    for path, ops in spec.get("paths", {}).items():
        for method in ops:
            if method.lower() in HTTP_METHODS:
                spec_endpoints.add(f"{method.upper()} {path}")

    if not ALLOWLIST.exists():
        print(f"FAIL: spec has {len(spec_endpoints)} endpoint(s) but "
              f"{ALLOWLIST.name} does not exist")
        return 1

    allow = json.loads(ALLOWLIST.read_text())
    for key in ("approved", "rejected"):
        if not isinstance(allow.get(key), list):
            print(f"FAIL: allowlist is malformed — '{key}' must be a list")
            return 1
    approved = {norm(e) for e in allow["approved"]}
    rejected = {norm(e) for e in allow["rejected"]}

    unapproved = sorted(spec_endpoints - approved)
    leaked_rejected = sorted(spec_endpoints & rejected)
    pending = sorted(approved - spec_endpoints)

    status = 0
    if unapproved:
        status = 1
        print("FAIL — in spec but NOT approved (remove from spec or get approval):")
        for e in unapproved:
            print(f"  {e}")
    if leaked_rejected:
        status = 1
        print("FAIL — in spec but explicitly REJECTED:")
        for e in leaked_rejected:
            print(f"  {e}")
    if pending:
        print("INFO — approved but not yet documented (next run's queue):")
        for e in pending:
            print(f"  {e}")
    if status == 0:
        print(f"OK: all {len(spec_endpoints)} spec endpoint(s) approved; "
              f"{len(pending)} approved endpoint(s) still to document")
    return status


if __name__ == "__main__":
    sys.exit(main())
