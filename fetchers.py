"""Source fetchers. Each downloads content to sources/ subdirectories."""

import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from parsers import parse_html

logger = logging.getLogger(__name__)

OPENAPI_URL = "https://pistrikkoolitus.envir.ee/docs/openapi.json"
WEB_DOCS_URL = "https://keskkonnaportaal.ee/et/teemad/reaalajamajandus/jaatmevaldkond"
GITHUB_API_REPO = "kemitgituser/pistrik-api-documentation"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_API_REPO}/main"

SUPPORTED_DOWNLOAD_EXTS = {".pdf", ".docx"}


def discover_file_formats(links: list[str]) -> tuple[set[str], set[str]]:
    """Classify linked file extensions into supported and unsupported."""
    supported = set()
    unsupported = set()
    for link in links:
        path = urlparse(link).path
        ext = Path(path).suffix.lower()
        if not ext:
            continue
        if ext in SUPPORTED_DOWNLOAD_EXTS:
            supported.add(ext)
        elif ext in {".html", ".htm", ""}:
            continue
        else:
            unsupported.add(ext)
    return supported, unsupported


def fetch_openapi(
    dest_dir: Path, url: str = OPENAPI_URL
) -> dict:
    """Fetch OpenAPI spec JSON."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    spec = resp.json()
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "openapi.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    return spec


def fetch_web_docs(
    dest_dir: Path, url: str = WEB_DOCS_URL
) -> dict:
    """Fetch web page + download linked documents. Returns report dict."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir = dest_dir / "attachments"
    attachments_dir.mkdir(exist_ok=True)

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # Save page as markdown
    md_content = parse_html(html)
    (dest_dir / "jaatmevaldkond.md").write_text(md_content, encoding="utf-8")

    # Find all links
    soup = BeautifulSoup(html, "html.parser")
    links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    full_links = [urljoin(url, link) for link in links]

    # Classify formats
    supported, unsupported = discover_file_formats(full_links)

    # Download supported files
    downloaded = []
    for link in full_links:
        ext = Path(urlparse(link).path).suffix.lower()
        if ext in SUPPORTED_DOWNLOAD_EXTS:
            try:
                file_resp = requests.get(link, timeout=60)
                file_resp.raise_for_status()
                filename = Path(urlparse(link).path).name
                dest = attachments_dir / filename
                dest.write_bytes(file_resp.content)
                downloaded.append(filename)
                logger.info(f"Downloaded: {filename}")
            except requests.RequestException as e:
                logger.warning(f"Failed to download {link}: {e}")

    return {
        "page_saved": "jaatmevaldkond.md",
        "downloaded": downloaded,
        "supported_formats": sorted(supported),
        "unsupported_formats": sorted(unsupported),
    }


def fetch_github_api_docs(
    dest_dir: Path,
    repo: str = GITHUB_API_REPO,
) -> list[str]:
    """Fetch Postman collections and environments from GitHub."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Fetch repo tree
    api_url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()
    tree = resp.json().get("tree", [])

    # Download JSON files
    downloaded = []
    for item in tree:
        if item["path"].endswith(".json"):
            raw_url = f"{GITHUB_RAW_BASE}/{item['path']}"
            file_resp = requests.get(raw_url, timeout=30)
            file_resp.raise_for_status()
            dest = dest_dir / Path(item["path"]).name
            dest.write_text(file_resp.text, encoding="utf-8")
            downloaded.append(dest.name)
            logger.info(f"Downloaded: {dest.name}")

    return downloaded
