# Copyright 2026 Millow AB
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""File and directory names are checked as plain strings.

A valid name is a single path component: not empty, not ``.`` or ``..``,
without ``/``, ``\\`` or NUL, and at most 255 bytes in UTF-8. Checking a name
must never create anything on disk.
"""

import os
import tempfile
import uuid

from odoo.exceptions import ValidationError

from ..tools.file import check_name
from .common import StorageFileBaseCase

VALID_NAMES = [
    "Quarterly report 2026.pdf",
    "Smith & Jones (draft).docx",
    "Översikt – mätning (v2).xlsx",
    "日本語のファイル.txt",
    "notes.tar.gz",
    ".hidden",
    "x" * 255,
    "å" * 127 + "x",  # 255 bytes in UTF-8
]

INVALID_NAMES = [
    "",
    False,
    None,
    ".",
    "..",
    "a/b",
    "a\\b",
    "a\0b",
    "x" * 256,
    "å" * 128,  # 256 bytes in UTF-8
    "\ud800",  # lone surrogate, cannot be encoded
]


class TestDmsNameCheck(StorageFileBaseCase):
    def _outside_path(self):
        """Return an absolute path in the system temp dir that does not exist.

        Removed after the test in case a check ever creates it.
        """
        path = os.path.join(tempfile.gettempdir(), f"dms-name-check-{uuid.uuid4().hex}")
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.assertFalse(os.path.exists(path))
        return path

    def _outside_names(self):
        """Names that point outside a directory: one relative, one absolute."""
        relative_target = self._outside_path()
        absolute_target = self._outside_path()
        relative_name = "../" * 16 + relative_target.lstrip("/")
        return [
            (relative_name, relative_target),
            (absolute_target, absolute_target),
        ]

    # ------------------------------------------------------------------
    # check_name()
    # ------------------------------------------------------------------
    def test_check_name_accepts_valid_names(self):
        for name in VALID_NAMES:
            with self.subTest(name=name):
                self.assertTrue(check_name(name))

    def test_check_name_refuses_invalid_names(self):
        for name in INVALID_NAMES:
            with self.subTest(name=name):
                self.assertFalse(check_name(name))

    def test_check_name_does_not_touch_disk(self):
        for name, target in self._outside_names():
            with self.subTest(name=name):
                self.assertFalse(check_name(name))
                self.assertFalse(os.path.exists(target))

    # ------------------------------------------------------------------
    # dms.file
    # ------------------------------------------------------------------
    def test_file_create_refuses_outside_names(self):
        for name, target in self._outside_names():
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.file_model.create(
                        {
                            "name": name,
                            "directory_id": self.directory.id,
                            "content": self.content_base64(),
                        }
                    )
                self.assertFalse(os.path.exists(target))

    def test_file_rename_refuses_outside_names(self):
        for name, target in self._outside_names():
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.file.write({"name": name})
                self.assertFalse(os.path.exists(target))

    def test_file_accepts_valid_names(self):
        for name in VALID_NAMES:
            with self.subTest(name=name):
                record = self.file_model.create(
                    {
                        "name": name,
                        "directory_id": self.directory.id,
                        "content": self.content_base64(),
                    }
                )
                self.assertEqual(record.name, name)
                record.unlink()

    # ------------------------------------------------------------------
    # dms.directory
    # ------------------------------------------------------------------
    def test_directory_create_refuses_outside_names(self):
        for name, target in self._outside_names():
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.directory_model.create(
                        {"name": name, "parent_id": self.directory.id}
                    )
                self.assertFalse(os.path.exists(target))

    def test_directory_rename_refuses_outside_names(self):
        child = self.create_directory(directory=self.directory)
        for name, target in self._outside_names():
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    child.write({"name": name})
                self.assertFalse(os.path.exists(target))

    def test_directory_accepts_valid_names(self):
        for name in VALID_NAMES:
            with self.subTest(name=name):
                record = self.directory_model.create(
                    {"name": name, "parent_id": self.directory.id}
                )
                self.assertEqual(record.name, name)
                record.unlink()
