#!/usr/bin/env python3
"""Structural linter for the Revve docs repo (Mintlify).

Deterministic checks used by .claude/skills/improve-docs and api-reference
(via scripts/verify.sh). Catches the failure modes that have actually bitten
this repo: nav entries without files, orphan pages, missing screenshots, raw
{{...}} outside code (blanks the whole MDX page body), duplicate headings,
frontmatter drift, and link-convention violations.

Usage:
  check_docs.py                 # whole repo
  check_docs.py --files a.mdx b.mdx
  check_docs.py --json

Exit codes: 0 clean, 1 errors present, 2 warnings only.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWN_ORPHANS_FILE = ROOT / "scripts" / "known-orphans.txt"
SCREENSHOT_DIR = ROOT / "screenshots"
SCREENSHOT_PREFIXES = (
    "voice-", "campaign-", "chatbot-", "chatbots-", "flow-", "knowledge-",
    "automation-", "website-", "inbox-", "email-", "sms-", "whatsapp-",
    "zalo-", "messenger-", "analytics-", "chat-", "dashboard-", "channel-",
    "new-agent-", "build-from-", "settings-", "evaluations-",
)
ALLOWED_LOWER_TAGS = {
    "a", "b", "br", "code", "div", "em", "hr", "i", "iframe", "img", "kbd",
    "li", "ol", "p", "pre", "source", "span", "strong", "sub", "sup",
    "table", "tbody", "td", "th", "thead", "tr", "u", "ul", "video",
}

findings = []


def add(check, file, line, detail, level="error"):
    findings.append({"check": check, "level": level, "file": str(file),
                     "line": line, "detail": detail})


def nav_pages(doc):
    """Recursively collect page path strings from docs.json navigation."""
    pages = []

    def walk(node):
        if isinstance(node, str):
            pages.append(node)
        elif isinstance(node, dict):
            for key in ("groups", "pages", "tabs", "anchors", "navigation"):
                if key in node:
                    walk(node[key])
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc.get("navigation", {}))
    return pages


def strip_code(text):
    """Blank out fenced code blocks and inline code spans, preserving line
    structure so reported line numbers stay accurate."""
    out, in_fence = [], False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        # remove inline code spans (`...` including double-backtick spans)
        line = re.sub(r"``.+?``", lambda m: " " * len(m.group()), line)
        line = re.sub(r"`[^`]*`", lambda m: " " * len(m.group()), line)
        out.append(line)
    return out


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    keys = {}
    for line in m.group(1).split("\n"):
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:", line)
        if km:
            keys[km.group(1)] = True
    return keys


def slugify(heading):
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[\s]+", "-", s).strip("-")


def check_page(path, all_page_ids):
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")

    fm = parse_frontmatter(text)
    if fm is None:
        add("frontmatter", rel, 1, "no frontmatter block")
    else:
        for req in ("title", "description"):
            if req not in fm:
                add("frontmatter", rel, 1, f"missing required key: {req}")
        extra = set(fm) - {"title", "description"}
        if extra:
            add("frontmatter", rel, 1,
                f"unexpected keys: {sorted(extra)}", level="warning")

    lines = strip_code(text)

    headings, images, links = [], [], []
    for i, line in enumerate(lines, 1):
        if "{{" in line:
            add("double-brace", rel, i,
                "raw {{ outside code — this blanks the entire page body; "
                "wrap in backticks")
        hm = re.match(r"^(#{1,6})\s+(.*)", line)
        if hm:
            headings.append((i, hm.group(2).strip()))
        for im in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", line):
            images.append((i, im.group(1), im.group(2)))
        for lm in re.finditer(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)", line):
            links.append((i, lm.group(1)))
        for tm in re.finditer(r"<([a-z][a-zA-Z0-9]*)", line):
            tag = tm.group(1)
            if tag not in ALLOWED_LOWER_TAGS:
                add("raw-angle-bracket", rel, i,
                    f"'<{tag}' outside code may parse as JSX and break the "
                    "page; backtick or escape it", level="warning")

    seen = {}
    for i, h in headings:
        if h in seen:
            add("duplicate-heading", rel, i,
                f'heading "{h}" repeats (first at line {seen[h]}) — anchor '
                "links can only reach the first", level="warning")
        else:
            seen[h] = i

    heading_slugs = {slugify(h) for _, h in headings}

    for i, alt, target in images:
        if target.startswith("/screenshots/"):
            if not (ROOT / target.lstrip("/")).exists():
                add("missing-image", rel, i, f"{target} does not exist")
            name = Path(target).name
            if not any(name.startswith(p) for p in SCREENSHOT_PREFIXES):
                add("screenshot-naming", rel, i,
                    f"{name} lacks a known feature prefix", level="warning")
        if not alt.strip() or alt.strip().lower() == Path(target).stem.lower():
            add("alt-text", rel, i,
                f"image {target} has empty or filename-like alt text",
                level="warning")

    for i, target in links:
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.endswith(".mdx"):
            add("link-convention", rel, i,
                f"link '{target}' must not use the .mdx suffix")
            continue
        if target.startswith(("./", "../")):
            add("link-convention", rel, i,
                f"link '{target}' is relative — use an absolute path "
                "(/section/page)")
            continue
        base, _, anchor = target.partition("#")
        if base:
            page_id = base.strip("/")
            if page_id not in all_page_ids:
                add("broken-link", rel, i, f"'{base}' has no matching page")
            elif anchor:
                other = ROOT / f"{page_id}.mdx"
                other_slugs = {
                    slugify(h)
                    for _, h in _headings_of(other)
                }
                if anchor not in other_slugs:
                    add("stale-anchor", rel, i,
                        f"'{target}' — no heading matches #{anchor}",
                        level="warning")
        elif anchor and anchor not in heading_slugs:
            add("stale-anchor", rel, i,
                f"'#{anchor}' matches no heading on this page",
                level="warning")


_heading_cache = {}


def _headings_of(path):
    if path not in _heading_cache:
        result = []
        if path.exists():
            for i, line in enumerate(strip_code(path.read_text()), 1):
                m = re.match(r"^(#{1,6})\s+(.*)", line)
                if m:
                    result.append((i, m.group(2).strip()))
        _heading_cache[path] = result
    return _heading_cache[path]


def repo_wide_checks(all_page_ids, mdx_files):
    docs_json = ROOT / "docs.json"
    for page in all_page_ids:
        if not (ROOT / f"{page}.mdx").exists():
            add("nav-missing-file", "docs.json", 0,
                f"nav entry '{page}' has no {page}.mdx")

    known = set()
    if KNOWN_ORPHANS_FILE.exists():
        known = {l.strip() for l in KNOWN_ORPHANS_FILE.read_text().split("\n")
                 if l.strip() and not l.startswith("#")}
    for f in mdx_files:
        page_id = str(f.relative_to(ROOT))[:-4]
        if page_id not in all_page_ids and page_id not in known:
            add("orphan-page", f.relative_to(ROOT), 0,
                "page exists but is not in docs.json nav (add it, delete it, "
                "or list it in scripts/known-orphans.txt)")

    referenced = set()
    for f in mdx_files:
        for m in re.finditer(r"/screenshots/([^)\s\"']+)", f.read_text()):
            referenced.add(m.group(1))
    if SCREENSHOT_DIR.exists():
        for img in sorted(SCREENSHOT_DIR.iterdir()):
            if img.name not in referenced:
                add("unused-screenshot", f"screenshots/{img.name}", 0,
                    "not referenced by any page", level="warning")
            else:
                dims = _dimensions(img)
                if dims and dims not in ((1440, 900), (2880, 1800)):
                    add("screenshot-dimensions", f"screenshots/{img.name}", 0,
                        f"{dims[0]}x{dims[1]} (convention: 1440x900 or 2x)",
                        level="warning")


def _dimensions(img):
    try:
        out = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(img)],
            capture_output=True, text=True, timeout=10).stdout
        w = re.search(r"pixelWidth: (\d+)", out)
        h = re.search(r"pixelHeight: (\d+)", out)
        return (int(w.group(1)), int(h.group(1))) if w and h else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*", help="only lint these .mdx files "
                    "(repo-wide checks still run against full nav)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    doc = json.loads((ROOT / "docs.json").read_text())
    all_page_ids = set(nav_pages(doc))
    mdx_files = sorted(p for p in ROOT.rglob("*.mdx")
                       if ".claude" not in p.parts and "node_modules" not in p.parts)

    if args.files:
        targets = [Path(f).resolve() for f in args.files]
    else:
        targets = mdx_files
        repo_wide_checks(all_page_ids, mdx_files)

    for f in targets:
        if f.exists():
            check_page(f, all_page_ids)
        else:
            add("missing-file", f, 0, "file passed via --files does not exist")

    errors = [f for f in findings if f["level"] == "error"]
    warnings = [f for f in findings if f["level"] == "warning"]

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            mark = "ERROR" if f["level"] == "error" else "warn "
            print(f"[{mark}] {f['check']}: {f['file']}:{f['line']} — {f['detail']}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) "
              f"across {len(targets)} page(s)")

    sys.exit(1 if errors else (2 if warnings else 0))


if __name__ == "__main__":
    main()
