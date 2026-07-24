from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import httpx

ONET_RELEASES = {
    "29.3": "https://www.onetcenter.org/dl_files/database/db_29_3_excel.zip",
    "30.3": "https://www.onetcenter.org/dl_files/database/db_30_3_excel.zip",
}


def download_onet_releases(destination: Path) -> dict[str, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        for release, url in ONET_RELEASES.items():
            archive = destination / f"onet_{release.replace('.', '_')}.zip"
            release_dir = destination / f"onet_{release.replace('.', '_')}"
            if not archive.exists():
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with archive.open("wb") as target:
                        shutil.copyfileobj(response.raw, target)
            if not release_dir.exists():
                release_dir.mkdir()
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(release_dir)
            extracted[release] = release_dir
    return extracted
