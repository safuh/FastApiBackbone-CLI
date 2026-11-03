from pathlib import Path
from unittest.mock import patch

import pytest

from fastapi_backbone_cli.generator import (
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


def test_force_only_allows_empty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "inventory-api"
    destination.mkdir()
    with patch(
        "fastapi_backbone_cli.generator._download_archive", side_effect=RuntimeError("offline")
    ):
        with pytest.raises(RuntimeError, match="offline"):
            generate_project(project_name="inventory-api", output=str(tmp_path), force=True)
    assert not destination.exists()


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
