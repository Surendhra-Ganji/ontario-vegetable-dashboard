from __future__ import annotations
from urllib.parse import parse_qs, unquote, urlparse
import requests
from app.services.settings import SETTINGS

class OntarioCKANService:
    def __init__(self):
        self.base_url = SETTINGS["ONTARIO_CKAN_BASE_URL"].rstrip("/")
        self.timeout = SETTINGS["CKAN_TIMEOUT"]

    def package_show(self, dataset_slug: str) -> dict:
        url = f"{self.base_url}/package_show"
        resp = requests.get(url, params={"id": dataset_slug}, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError(f"CKAN package_show unsuccessful for {dataset_slug}")
        return payload["result"]

    def resolve_download_url(self, package_result: dict) -> str:
        resources = package_result.get("resources", [])
        if not resources:
            raise RuntimeError("No resources found in CKAN package")

        for resource in resources:
            url = (resource.get("url") or "").strip()
            fmt = (resource.get("format") or "").strip().lower()
            name = (resource.get("name") or "").strip().lower()
            if fmt == "xlsx" or url.lower().endswith(".xlsx") or "xlsx" in name:
                return self._normalize_download_url(url)

        for resource in resources:
            url = (resource.get("url") or "").strip()
            if url:
                return self._normalize_download_url(url)

        raise RuntimeError("No usable resource URL found")

    def _normalize_download_url(self, url: str) -> str:
        parsed = urlparse(url)
        if "view.officeapps.live.com" in parsed.netloc.lower():
            query = parse_qs(parsed.query)
            src = query.get("src", [None])[0]
            if src:
                return unquote(src)
        return url
