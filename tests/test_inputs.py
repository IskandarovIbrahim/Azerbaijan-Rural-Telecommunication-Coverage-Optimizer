"""Offline checks for the pinned source cache."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from coverage_optimizer.inputs import load_sources


class SourceCacheTests(unittest.TestCase):
    def test_offline_load_checks_cached_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cached = root / "synthetic.txt"
            contents = b"synthetic terrain bytes"
            cached.write_bytes(contents)
            manifest = root / "synthetic-manifest.json"
            manifest.write_text(json.dumps({"inputs": [{
                "filename": cached.name,
                "role": "elevation",
                "sha256": hashlib.sha256(contents).hexdigest(),
            }]}), encoding="utf-8")

            self.assertEqual(load_sources(manifest, root, offline=True), {"elevation": [cached]})
            cached.write_bytes(b"different synthetic bytes")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                load_sources(manifest, root, offline=True)
