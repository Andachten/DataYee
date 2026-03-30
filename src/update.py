"""Update checker for DataYee.

Checks GitHub releases for new versions.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

CURRENT_VERSION = "0.1.0"
REPO_OWNER = "Andachten"
REPO_NAME = "DataYee"


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    tag_name: str
    name: str
    html_url: str
    body: str
    published_at: str


def get_current_version() -> str:
    """Get the current DataYee version."""
    return CURRENT_VERSION


def fetch_latest_release() -> Optional[ReleaseInfo]:
    """Fetch the latest release from GitHub.

    Returns:
        ReleaseInfo if successful, None if failed.
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"{REPO_OWNER}/{REPO_NAME}"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
            return ReleaseInfo(
                tag_name=data.get("tag_name", "").lstrip("v"),
                name=data.get("name", ""),
                html_url=data.get("html_url", ""),
                body=data.get("body", ""),
                published_at=data.get("published_at", ""),
            )
    except Exception as e:
        print(f"Failed to fetch release info: {e}")
        return None


def check_for_updates() -> tuple[bool, Optional[ReleaseInfo]]:
    """Check if a new version is available.

    Returns:
        Tuple of (is_update_available, release_info)
    """
    latest = fetch_latest_release()
    if latest is None:
        return False, None

    current = get_current_version()
    is_update = _compare_versions(current, latest.tag_name) < 0

    return is_update, latest


def _compare_versions(current: str, latest: str) -> int:
    """Compare version strings.

    Returns:
        -1 if current < latest
         0 if current == latest
         1 if current > latest
    """
    def parse(v: str) -> tuple:
        return tuple(int(x) for x in v.split(".") if x.isdigit())

    current_parts = parse(current)
    latest_parts = parse(latest)

    if current_parts < latest_parts:
        return -1
    elif current_parts > latest_parts:
        return 1
    return 0


def format_update_message(release: ReleaseInfo) -> str:
    """Format the update message for display."""
    current = get_current_version()
    message = f"""版本信息:
当前版本: {current}
最新版本: {release.tag_name}

"""
    if release.name:
        message += f"发布说明:\n{release.name}\n\n"

    if release.body:
        message += f"{release.body[:200]}..."

    message += f"\n\n下载链接:\n{release.html_url}"

    return message
