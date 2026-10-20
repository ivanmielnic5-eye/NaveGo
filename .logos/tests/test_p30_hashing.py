#!/usr/bin/env python3
"""Prueba específica P30 para enlaces simbólicos a directorios."""

import hashlib
import importlib.util
import os
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = ROOT / ".logos/lib/logos_hash_lib.py"

spec = importlib.util.spec_from_file_location(
    "p30_hash_lib_under_test", LIB_PATH
)
if spec is None or spec.loader is None:
    raise RuntimeError(f"No se pudo cargar: {LIB_PATH}")

LIB = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LIB)


class DirectorySymlinkTests(unittest.TestCase):
    def test_symlink_is_hashed_as_metadata_without_traversal(self):
        with tempfile.TemporaryDirectory(prefix="p30-hash-") as tmp:
            base = pathlib.Path(tmp)
            root = base / "raiz"
            root.mkdir()

            target_a = base / "destino_a"
            target_a.mkdir()
            (target_a / "oculto.txt").write_text(
                "alfa\n", encoding="utf-8"
            )

            target_b = base / "destino_b"
            target_b.mkdir()
            (target_b / "oculto.txt").write_text(
                "beta\n", encoding="utf-8"
            )

            (root / "normal.txt").write_text(
                "visible\n", encoding="utf-8"
            )
            link = root / "enlace_dir"
            os.symlink("../destino_a", link)

            digest, count, kind = LIB.hash_source(str(root))

            self.assertEqual(kind, "DIRECTORIO")
            self.assertEqual(
                count, 2,
                "Debe contar el archivo normal y el enlace, "
                "sin recorrer el destino."
            )

            entries = [
                ("enlace_dir", link),
                ("normal.txt", root / "normal.txt"),
            ]
            entries.sort(key=lambda item: item[0].encode("utf-8"))

            expected = hashlib.sha256()
            for relative, full in entries:
                expected.update(relative.encode("utf-8"))
                expected.update(b"\x00")

                if os.path.islink(full):
                    expected.update(
                        b"LINK:" + os.readlink(full).encode("utf-8")
                    )
                    expected.update(b"\x00")
                else:
                    data = full.read_bytes()
                    expected.update(str(len(data)).encode("utf-8"))
                    expected.update(b"\x00")
                    expected.update(data)

            self.assertEqual(digest, expected.hexdigest())

            link.unlink()
            os.symlink("../destino_b", link)

            changed_digest, changed_count, changed_kind = (
                LIB.hash_source(str(root))
            )
            self.assertEqual(changed_kind, "DIRECTORIO")
            self.assertEqual(changed_count, 2)
            self.assertNotEqual(
                digest, changed_digest,
                "Cambiar el destino del enlace debe cambiar el hash."
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
