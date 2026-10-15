"""Deterministic, bounded discovery which never follows symbolic links."""

import os
from pathlib import Path

from ragvidence.ingestion.models import InputNotice

TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
EXCLUDED_DIRECTORIES = {"ragvi-reports", "workspaces", "node_modules", "__pycache__"}


def discover_files(
    source: Path, *, exclude: list[Path], max_files: int = 1000
) -> tuple[list[Path], list[InputNotice]]:
    if source.is_symlink():
        raise ValueError(f"Symbolic-link input is not supported: {source}")
    if not source.exists():
        raise ValueError(f"Input does not exist: {source}")
    excluded = {path.resolve() for path in exclude}
    skipped = []
    if source.is_file():
        if source.resolve() in excluded:
            raise ValueError("The source input cannot also be a question file or output directory")
        if source.suffix.lower() not in TEXT_EXTENSIONS:
            raise ValueError(f"Unsupported input {source.suffix!r}; currently use TXT or Markdown")
        return [source], skipped
    if not source.is_dir():
        raise ValueError(f"Input must be a regular file or directory: {source}")
    files = []

    def walk_error(error: OSError) -> None:
        raise ValueError(f"Cannot read input directory: {error.filename}") from error

    for root, directories, names in os.walk(source, followlinks=False, onerror=walk_error):
        retained = []
        for name in sorted(directories):
            path = Path(root) / name
            if (
                name.startswith(".")
                or name in EXCLUDED_DIRECTORIES
                or path.is_symlink()
                or (path / ".ragvi-run.json").is_file()
                or path.resolve() in excluded
            ):
                skipped.append(
                    InputNotice(
                        path=str(path.relative_to(source)),
                        reason="Excluded directory or symbolic link",
                    )
                )
            else:
                retained.append(name)
        directories[:] = retained
        for name in sorted(names):
            path = Path(root) / name
            if name.startswith(".") or path.is_symlink() or path.resolve() in excluded:
                reason = "Excluded file or symbolic link"
            elif path.suffix.lower() not in TEXT_EXTENSIONS:
                reason = "Unsupported file type"
            else:
                files.append(path)
                if len(files) > max_files:
                    raise ValueError(f"Input exceeds the {max_files} supported-file limit")
                continue
            skipped.append(InputNotice(path=str(path.relative_to(source)), reason=reason))
    return sorted(files), skipped
