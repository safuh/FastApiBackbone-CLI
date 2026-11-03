from pathlib import Path
from unittest.mock import patch

import pytest

from fastapi_backbone_cli.generator import (
    _customize_project,
    _extract_archive,
    _normalize_project_name,
    generate_project,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("inventory-api", ("inventory_api", "Inventory Api")),
        ("billing_service", ("billing_service", "Billing Service")),
    ],
)
def test_normalize_project_name(value: str, expected: tuple[str, str]) -> None:
    assert _normalize_project_name(value) == expected


@pytest.mark.parametrize("value", ["", "../escape", "-bad", "a", "contains space", "x" * 64])
def test_rejects_invalid_project_names(value: str) -> None:
    with pytest.raises(ValueError):
        _normalize_project_name(value)


def test_existing_nonempty_destination_is_not_overwritten(tmp_path: Path) -> None:
    destination = tmp_path / "inventory-api"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        generate_project(project_name="inventory-api", output=str(tmp_path))
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_force_only_allows_empty_destination_and_preserves_it_on_failure(tmp_path: Path) -> None:
    destination = tmp_path / "inventory-api"
    destination.mkdir()
    with patch(
        "fastapi_backbone_cli.generator._download_archive", side_effect=RuntimeError("offline")
    ):
        with pytest.raises(RuntimeError, match="offline"):
            generate_project(project_name="inventory-api", output=str(tmp_path), force=True)
    assert destination.is_dir()
    assert not any(destination.iterdir())


def test_customize_renames_package_and_removes_unselected_assets(tmp_path: Path) -> None:
    package = tmp_path / "src" / "fastapi_backbone"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("import fastapi_backbone", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        'name = "fastapi-backbone"\n'
        'include = ["fastapi_backbone*"]\n'
        'known-first-party = ["fastapi_backbone"]\n',
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text('name = "fastapi-backbone"\n', encoding="utf-8")
    (tmp_path / "README.md").write_text("FastAPI Backbone", encoding="utf-8")
    for relative in ("docker/Dockerfile", "k8s/base/deployment.yaml", "docs/DOCKER.md"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder", encoding="utf-8")

    _customize_project(
        tmp_path,
        "inventory_api",
        "Inventory Api",
        "inventory-api",
        include_docker=False,
        include_kubernetes=False,
    )

    assert (tmp_path / "src" / "inventory_api" / "__init__.py").read_text() == (
        "import inventory_api"
    )
    assert not (tmp_path / "src" / "fastapi_backbone").exists()
    project_config = (tmp_path / "pyproject.toml").read_text()
    assert 'name = "inventory-api"' in project_config
    assert 'include = ["inventory_api*"]' in project_config
    assert 'known-first-party = ["inventory_api"]' in project_config
    assert 'name = "inventory-api"' in (tmp_path / "uv.lock").read_text()
    assert "# Inventory Api" in (tmp_path / "README.md").read_text()
    assert not (tmp_path / "docker").exists()
    assert not (tmp_path / "k8s").exists()
    assert not (tmp_path / "docs" / "DOCKER.md").exists()


def test_archive_rejects_path_traversal(tmp_path: Path) -> None:
    import io
    import tarfile

    archive_path = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo("../outside")
        info.size = 1
        archive.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(RuntimeError, match="unsafe path"):
        _extract_archive(archive_path, tmp_path / "out")
