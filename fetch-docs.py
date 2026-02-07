#!/usr/bin/env python3
"""
Fetch Claude Code documentation from code.claude.com/docs.

Downloads all pages listed in llms.txt to ~/.claude/docs/claude-code/.
No dependencies beyond Python 3.6+ standard library.

Usage:
    python fetch-docs.py           # Download all docs
    python fetch-docs.py --check   # Check for updates (no download)
    python fetch-docs.py --update  # Download only changed pages
"""
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

DOCS_DIR = Path.home() / ".claude" / "docs" / "claude-code"
INDEX_URL = "https://code.claude.com/docs/llms.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch(url: str) -> str:
    """Fetch a URL and return its text content."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def head(url: str) -> dict:
    """Send a HEAD request, return headers as dict."""
    req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return dict(resp.headers)


def parse_index(text: str) -> list:
    """Parse llms.txt and return list of (title, url) tuples."""
    pages = []
    for line in text.strip().splitlines():
        m = re.match(r"^- \[(.+?)\]\((https://[^\)]+\.md)\)", line)
        if m:
            pages.append((m.group(1), m.group(2)))
    return pages


def url_to_filename(url: str) -> str:
    """Convert URL to local filename. e.g. .../en/hooks.md -> hooks.md"""
    return url.rsplit("/", 1)[-1]


def get_remote_modified(url: str):
    """Get Last-Modified datetime from HEAD request, or None."""
    try:
        h = head(url)
        lm = h.get("Last-Modified") or h.get("last-modified")
        if lm:
            return parsedate_to_datetime(lm)
    except Exception:
        pass
    return None


def get_local_modified(filepath: Path):
    """Get local file modification time as aware datetime, or None."""
    if filepath.exists():
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc)
    return None


def check_for_updates(pages):
    """Check which pages have updates. Returns (new, updated, removed, unchanged) lists."""
    new_pages = []
    updated_pages = []
    unchanged = 0

    for i, (title, url) in enumerate(pages, 1):
        filename = url_to_filename(url)
        local_path = DOCS_DIR / filename
        print(f"  [{i}/{len(pages)}] {filename}...", end=" ", flush=True)

        if not local_path.exists():
            print("NEW")
            new_pages.append(filename)
            continue

        remote_dt = get_remote_modified(url)
        local_dt = get_local_modified(local_path)

        if remote_dt and local_dt and remote_dt > local_dt:
            print(f"UPDATED (remote: {remote_dt.strftime('%Y-%m-%d %H:%M')})")
            updated_pages.append(filename)
        elif remote_dt is None:
            print("(no Last-Modified header, skipped)")
        else:
            print("current")
            unchanged += 1

        if i < len(pages):
            time.sleep(0.1)

    # Check for removed pages
    local_files = {f.name for f in DOCS_DIR.glob("*.md") if f.name != "_index.md"}
    remote_files = {url_to_filename(url) for _, url in pages}
    removed = sorted(local_files - remote_files)

    return new_pages, updated_pages, removed, unchanged


def download_pages(pages, only_files=None):
    """Download pages. If only_files is set, only download those filenames."""
    success = 0
    failed = []

    for i, (title, url) in enumerate(pages, 1):
        filename = url_to_filename(url)
        if only_files and filename not in only_files:
            continue

        target = DOCS_DIR / filename
        print(f"  {filename}...", end=" ", flush=True)

        try:
            content = fetch(url)
            target.write_text(content, encoding="utf-8")
            print("OK")
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((filename, str(e)))

        time.sleep(0.3)

    return success, failed


def write_manifest(pages, count):
    """Write the _index.md manifest."""
    manifest = f"# Claude Code Documentation\n"
    manifest += f"# Downloaded: {time.strftime('%Y-%m-%d %H:%M')}\n"
    manifest += f"# Source: {INDEX_URL}\n"
    manifest += f"# Pages: {count}/{len(pages)}\n\n"
    for title, url in pages:
        filename = url_to_filename(url)
        manifest += f"- {filename}: {title}\n"
    (DOCS_DIR / "_index.md").write_text(manifest, encoding="utf-8")


def main():
    mode = "all"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            mode = "check"
        elif sys.argv[1] == "--update":
            mode = "update"

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching index from {INDEX_URL}...")
    index_text = fetch(INDEX_URL)

    # Check if index itself changed
    local_index = DOCS_DIR / "llms.txt"
    if local_index.exists():
        old_text = local_index.read_text(encoding="utf-8")
        if old_text != index_text:
            print("Index has changed since last download.")
        else:
            print("Index unchanged.")

    pages = parse_index(index_text)
    print(f"Found {len(pages)} documentation pages.\n")

    if mode == "check":
        print("Checking for updates (HEAD requests only)...\n")
        new, updated, removed, unchanged = check_for_updates(pages)

        print(f"\n--- Summary ---")
        print(f"  Unchanged: {unchanged}")
        if new:
            print(f"  New pages ({len(new)}): {', '.join(new)}")
        if updated:
            print(f"  Updated ({len(updated)}): {', '.join(updated)}")
        if removed:
            print(f"  Removed from index ({len(removed)}): {', '.join(removed)}")
        if not new and not updated and not removed:
            print("  Everything is up to date.")
        return 0

    elif mode == "update":
        print("Checking for updates...\n")
        new, updated, removed, unchanged = check_for_updates(pages)

        targets = set(new) | set(updated)
        if not targets:
            print("\nEverything is up to date. Nothing to download.")
            return 0

        print(f"\nDownloading {len(targets)} changed page(s)...\n")
        success, failed = download_pages(pages, only_files=targets)
        local_index.write_text(index_text, encoding="utf-8")
        write_manifest(pages, len(pages))
        print(f"\nUpdated {success} page(s).")
        if failed:
            print(f"Failed ({len(failed)}):")
            for name, err in failed:
                print(f"  {name}: {err}")
        return 0 if not failed else 1

    else:  # mode == "all"
        local_index.write_text(index_text, encoding="utf-8")

        success = 0
        failed = []
        for i, (title, url) in enumerate(pages, 1):
            filename = url_to_filename(url)
            target = DOCS_DIR / filename
            print(f"  [{i}/{len(pages)}] {filename}...", end=" ", flush=True)

            try:
                content = fetch(url)
                target.write_text(content, encoding="utf-8")
                print("OK")
                success += 1
            except Exception as e:
                print(f"FAILED: {e}")
                failed.append((filename, str(e)))

            if i < len(pages):
                time.sleep(0.3)

        print(f"\nDone: {success}/{len(pages)} pages saved to {DOCS_DIR}")
        if failed:
            print(f"\nFailed ({len(failed)}):")
            for name, err in failed:
                print(f"  {name}: {err}")

        write_manifest(pages, success)
        return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
