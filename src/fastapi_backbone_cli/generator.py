"""Download, validate, and customize a pinned FastApiBackbone source snapshot."""

from __future__ import annotations

import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from urllib.parse import quote
from pathlib import Path, PurePosixPath

DEFAULT_TEMPLATE_REF = "89832bc467d21453e73f2e822cae4224d0c5a955"
TEMPLATE_REPOSITORY = "safuh/FastApiBackbone"
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 200 * 1024 * 1024
PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,62}$")


def _normalize_project_name(project_name: str) -> tuple[str, str]:
    candidate = project_name.strip()
    if not PROJECT_NAME_PATTERN.fullmatch(candidate):
        raise ValueError(
            "Project name must start with a letter and contain 2–63 letters, "
            "numbers, underscores, or hyphens."
        )
    module_name = candidate.replace("-", "_").lower()
    display_name = candidate.replace("-", " ").replace("_", " ").title()
    return module_name, display_name


def _download_archive(template_ref: str, destination: Path) -> None:
    if not template_ref or template_ref.startswith("-"):
        raise ValueError("Template ref must be a branch, tag, or commit identifier.")
    encoded_ref = quote(template_ref, safe="")
    url = f"https://github.com/{TEMPLATE_REPOSITORY}/archive/{encoded_ref}.tar.gz"
    request = urllib.request.Request(url, headers={"User-Agent": "FastApiBackbone-CLI/0.1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_ARCHIVE_BYTES:
                raise RuntimeError("Template archive exceeds the 50 MiB download limit.")
            data = response.read(MAX_ARCHIVE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Unable to download template {template_ref!r}: {exc}") from exc
    if len(data) > MAX_ARCHIVE_BYTES:
        raise RuntimeError("Template archive exceeds the 50 MiB download limit.")
    destination.write_bytes(data)


def _extract_archive(archive_path: Path, destination: Path) -> Path:
    extracted_size = 0
    root: Path | None = None
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError("Template archive contains an unsafe path.")
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise RuntimeError("Template archive contains an unsupported entry.")
            extracted_size += member.size
            if extracted_size > MAX_EXTRACTED_BYTES:
                raise RuntimeError("Template archive exceeds the 200 MiB extraction limit.")
        for member in members:
            archive.extract(member, destination, filter="data")
            if root is None and member.name:
                root = destination / PurePosixPath(member.name).parts[0]
    if root is None or not (root / "pyproject.toml").is_file():
        raise RuntimeError("Downloaded archive is not a valid FastApiBackbone template.")
    return root


def _customize_project(
    root: Path,
    module_name: str,
    display_name: str,
    project_name: str,
    include_docker: bool,
    include_kubernetes: bool,
) -> None:
    source_package = root / "src" / "fastapi_backbone"
    target_package = root / "src" / module_name
    if not source_package.is_dir():
        raise RuntimeError("Template does not contain src/fastapi_backbone.")
    source_package.rename(target_package)

    replacements = {
        "fastapi_backbone": module_name,
        "FastAPI Backbone": display_name,
    }
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        if path.name == "pyproject.toml":
            distribution_name = project_name.lower().replace("_", "-")
            content = re.sub(
                r'(?m)^name\s*=\s*"fastapi-backbone"\s*$',
                f'name = "{distribution_name}"',
                content,
                count=1,
            )
            content = content.replace(
                'include = ["fastapi_backbone*"]', f'include = ["{module_name}*"]'
            )
            content = content.replace(
                'known-first-party = ["fastapi_backbone"]',
                f'known-first-party = ["{module_name}"]',
            )
        if path.name == "uv.lock":
            distribution_name = project_name.lower().replace("_", "-")
            content = content.replace('name = "fastapi-backbone"', f'name = "{distribution_name}"')
        if path.name == "uv.lock":
            distribution_name = project_name.lower().replace("_", "-")
            content = content.replace('name = "fastapi-backbone"', f'name = "{distribution_name}"')
        if content != original:
            path.write_text(content, encoding="utf-8")

    if not include_docker:
        for relative in (
            ".dockerignore", "docker", "scripts/docker-production.sh", "scripts/docker-smoke.sh"
        ):
            target = root / relative
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
    readme = f"""# {display_name}

A backend service generated from [FastApiBackbone](https://github.com/safuh/FastApiBackbone).

**Stack:** FastAPI · Pydantic · SQLAlchemy 2.x · Alembic · PostgreSQL

## Quick start

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), and Docker if you use the container workflow.

```bash
uv sync --extra dev
cp .env.example .env
make check
make run
```

The API documentation is available at http://127.0.0.1:8000/docs.

## Database

SQLite is configured for local development. Configure `DATABASE_URL` in `.env` for PostgreSQL, then run:

```bash
make migrate-up
```

## Docker

Docker assets are {"included" if include_docker else "not included"}.
{"Kubernetes/Kustomize manifests are included." if include_kubernetes else "Kubernetes/Kustomize manifests are not included."}

## Architecture

The project includes a FastAPI application factory, Pydantic Settings, async SQLAlchemy persistence,
Alembic migrations, health/readiness endpoints, structured logging, authentication primitives,
and tests. Review the security documentation before enabling authentication in production.

This project is an independent copy. It does not retain the source repository's Git history.
"""
    (root / "README.md").write_text(readme, encoding="utf-8")

    if not include_kubernetes:
        shutil.rmtree(root / "k8s", ignore_errors=True)
        (root / "docs" / "KUBERNETES.md").unlink(missing_ok=True)


def generate_project(
    *,
    project_name: str,
    output: str | None = None,
    template_ref: str = DEFAULT_TEMPLATE_REF,
    include_docker: bool = True,
    include_kubernetes: bool = False,
    force: bool = False,
) -> Path:
    """Generate a project directory and return its resolved path."""
    module_name, display_name = _normalize_project_name(project_name)
    parent = Path(output).expanduser() if output else Path.cwd()
    parent.mkdir(parents=True, exist_ok=True)
    destination = (parent / project_name).resolve()

    destination_preexisted = destination.exists()
    if destination_preexisted:
        if not force:
            raise FileExistsError(f"Destination already exists: {destination}")
        if not destination.is_dir() or any(destination.iterdir()):
            raise FileExistsError("--force only permits an existing empty directory.")
    else:
        destination.mkdir(parents=True)

    try:
        with tempfile.TemporaryDirectory(prefix="fastapi-backbone-") as temporary:
            temporary_path = Path(temporary)
            archive_path = temporary_path / "template.tar.gz"
            extraction_path = temporary_path / "extract"
            extraction_path.mkdir()
            _download_archive(template_ref, archive_path)
            source_root = _extract_archive(archive_path, extraction_path)
            _customize_project(
                source_root, module_name, display_name, project_name,
                include_docker, include_kubernetes,
            )
            shutil.copytree(
                source_root,
                destination,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git", ".github", "__pycache__", ".venv"),
            )
    except Exception:
        if destination.exists() and not destination_preexisted:
            shutil.rmtree(destination)
        raise
    return destination
