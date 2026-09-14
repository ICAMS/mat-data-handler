"""Resolve the mat-data material dataset over the network (no pip/conda dependency).

The material entries, JSON schemas, and PROPS mapping table live in the
separate `mat-data` repository (https://github.com/ICAMS/mat-data), not as an
installable package. This module fetches (and caches) that repository's
content, or uses a local checkout directly during development.

Resolution order:
1. ``MAT_DATA_LOCAL_PATH`` env var, if set: use that directory as-is (no
   network access). Intended for local development against a sibling
   checkout of ``mat-data``, and for CI, which checks out ``mat-data``
   itself and points this at it.
2. Cached download for the requested ref under ``MAT_DATA_CACHE_DIR``
   (defaults to ``~/.cache/mat-data-handler``).
3. Fresh download via ``MAT_DATA_FETCH_METHOD`` (``http`` tarball download by
   default, stdlib-only; or ``git clone`` if explicitly requested).
"""

from __future__ import annotations

import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path

DEFAULT_REPO = "ICAMS/mat-data"
DEFAULT_REF = "main"


def _cache_dir() -> Path:
    return Path(os.environ.get("MAT_DATA_CACHE_DIR", Path.home() / ".cache" / "mat-data-handler"))


def _fetch_http(repo: str, ref: str, dest: Path) -> None:
    """Download and extract the repo's tarball for ``ref`` via GitHub's codeload API."""
    url = f"https://codeload.github.com/{repo}/tar.gz/{ref}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    archive = dest.parent / f"{dest.name}.tar.gz"
    with urllib.request.urlopen(url) as response, open(archive, "wb") as stream:
        stream.write(response.read())
    try:
        with tarfile.open(archive) as tar:
            # GitHub tarballs contain a single top-level "<repo>-<ref>/" directory.
            members = tar.getmembers()
            top = os.path.commonpath([m.name for m in members])
            safe_members = [m for m in members if not (m.name.startswith("/") or ".." in Path(m.name).parts)]
            tar.extractall(dest.parent, members=safe_members)  # noqa: S202 -- paths sanitized above
        (dest.parent / top).replace(dest)
    finally:
        archive.unlink(missing_ok=True)


def _fetch_git(repo: str, ref: str, dest: Path) -> None:
    """Shallow-clone the repo at ``ref`` (branch or tag) using the system ``git`` binary."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, f"https://github.com/{repo}.git", str(dest)],
        check=True,
    )


def data_root(repo: str = None, ref: str = None) -> Path:
    """Return a local directory containing entries/, schemas/, mapping.csv."""
    local = os.environ.get("MAT_DATA_LOCAL_PATH")
    if local:
        return Path(local)

    repo = repo or os.environ.get("MAT_DATA_REPO", DEFAULT_REPO)
    ref = ref or os.environ.get("MAT_DATA_REF", DEFAULT_REF)
    method = os.environ.get("MAT_DATA_FETCH_METHOD", "http")

    dest = _cache_dir() / repo.replace("/", "__") / ref
    if not dest.is_dir():
        fetch = _fetch_git if method == "git" else _fetch_http
        fetch(repo, ref, dest)
    return dest


def entries_dir(repo: str = None, ref: str = None) -> Path:
    return data_root(repo, ref) / "entries"


def schemas_dir(repo: str = None, ref: str = None) -> Path:
    return data_root(repo, ref) / "schemas"


def mapping_path(repo: str = None, ref: str = None) -> Path:
    return data_root(repo, ref) / "mapping.csv"
