"""Tests for the bounded Warcraft III campaign-map audit."""

from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wc3_map_audit", ROOT / "tools/wc3_map_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(AUDIT)


def cstring(text: str) -> bytes:
    return text.encode() + b"\0"


def w3i_fixture(name: str, title: str, subtitle: str) -> bytes:
    data = struct.pack("<III", 18, 0, 0)
    data += b"".join(cstring(text) for text in (name, "author", "description", "players"))
    data += bytes(48 + 8 + 4 + 1 + 4)
    data += b"".join(cstring(text) for text in ("loading text", title, subtitle))
    return data


class MapMetadataTest(unittest.TestCase):
    def test_wts_zero_id_and_loading_title_are_resolved(self):
        wts = "\ufeffSTRING 0\n{\nChapter Five\n}\nSTRING 1\n{\nMarch of the Scourge\n}\n"
        name = AUDIT.parse_w3i_name(w3i_fixture("Human05", "TRIGSTR_000", "TRIGSTR_001"), wts, "fallback")
        self.assertEqual(name, "Chapter Five — March of the Scourge")

    def test_map_name_is_used_without_loading_titles(self):
        self.assertEqual(AUDIT.parse_w3i_name(w3i_fixture("Human05", "", ""), "", "fallback"), "Human05")


class DiagnosticTest(unittest.TestCase):
    def test_repeated_entity_errors_are_compacted(self):
        output = """
SLK: failed to load 'UI\\SoundInfo\\Music.slk'
WC3 CreepSleep: ACsp TargetArt missing; using canonical sleep art for unit 2
WC3 CreepSleep: ACsp TargetArt missing; using canonical sleep art for unit 9
SV_FindIndex: pool full start=32 max=256 name=a.mdx
SV_FindIndex: pool full start=32 max=256 name=b.mdx
JASS runtime error: unimplemented native: EnumItemsInRect
JASS runtime error: unimplemented native: EnumItemsInRect
"""
        errors, families = AUDIT.compact_diagnostics(output, "completed", 0, False)
        self.assertIn("CREEP_SLEEP_ART ×2", errors)
        self.assertIn("MODEL_POOL_FULL ×2 (2 resources)", errors)
        self.assertIn("JASS `EnumItemsInRect` ×2", errors)
        self.assertIn("JASS:EnumItemsInRect", families)

    def test_serially_reproduced_signal_is_reported(self):
        errors, families = AUDIT.compact_diagnostics("", "crashed", -11, True)
        self.assertEqual(errors, ["SIGSEGV (exit -11; reproduced serially)"])
        self.assertEqual(families, {"SIGSEGV"})

    def test_ordinary_nonzero_exit_is_not_called_sigsegv(self):
        errors, families = AUDIT.compact_diagnostics("", "crashed", 2, False)
        self.assertEqual(errors, ["PROCESS_EXIT (code 2)"])
        self.assertEqual(families, {"PROCESS_EXIT"})


class ReportTest(unittest.TestCase):
    def test_report_names_file_and_does_not_claim_completion(self):
        report = {
            "commit": "abc123",
            "frames": 600,
            "simulated_seconds": 60,
            "timeout_seconds": 120,
            "jobs": 4,
            "wall_seconds": 1.5,
            "maps": [{
                "edition": "RoC",
                "name": "Chapter Five — March of the Scourge",
                "filename": "Human05.w3m",
                "status": "completed",
                "compact_errors": ["JASS `SetCaptainHome` ×2"],
                "families": ["JASS:SetCaptainHome"],
            }],
        }
        markdown = AUDIT.render_markdown(report)
        self.assertIn("March of the Scourge", markdown)
        self.assertIn("`Human05.w3m`", markdown)
        self.assertIn("600 frames", markdown)
        self.assertNotIn("map works", markdown.lower())


if __name__ == "__main__":
    unittest.main()
