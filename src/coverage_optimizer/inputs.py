"""Acquire pinned inputs and verify the local cache."""

import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_sources(manifest_path: Path, cache: Path, offline: bool) -> dict[str, list[Path]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths: dict[str, list[Path]] = {}
    for source in manifest["inputs"]:
        filename = Path(source["filename"])
        if filename.name != str(filename) or filename.name in ("", ".."):
            raise ValueError(f"invalid source filename: {filename}")
        target = cache / filename
        if not target.exists():
            if offline:
                raise ValueError(f"missing cached input {target}. Run without --offline to retrieve it.")
            cache.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=cache) as temp:
                draft = Path(temp) / filename
                try:
                    subprocess.run(
                        ["curl", "--fail", "--location", "--silent", "--show-error",
                         "--proto", "=https", "--proto-redir", "=https", "--retry", "2",
                         "--max-time", "180", "--output", str(draft), source["url"]],
                        check=True,
                    )
                except FileNotFoundError as exc:
                    raise OSError("curl is required to fetch missing inputs") from exc
                except subprocess.CalledProcessError as exc:
                    raise OSError(f"could not download {filename} (curl exit {exc.returncode})") from exc
                verify_checksum(draft, source["sha256"])
                draft.replace(target)
        else:
            verify_checksum(target, source["sha256"])
        paths.setdefault(source["role"], []).append(target)
    return paths


def verify_checksum(path: Path, expected: str) -> None:
    if sha256(path) != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}. Check the pinned manifest and cached file.")
