from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rag.build_index import build_index
from rag.retriever import RagRetriever


class RagPipelineTests(unittest.TestCase):
    def test_build_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            documents = root / "documents"
            documents.mkdir()
            (documents / "policy.md").write_text(
                "病假規章：醫療證明須依 HR 核准政策辦理。\n\n特休申請由主管與 HR 審核。",
                encoding="utf-8",
            )
            index_path = root / "index.json"
            payload = build_index(documents, index_path, max_chars=300, overlap_chars=30)
            self.assertEqual(payload["documents"], 1)
            self.assertGreaterEqual(len(payload["chunks"]), 1)

            result = RagRetriever(index_path).answer("病假醫療證明")
            self.assertTrue(result["matches"])
            self.assertIn("醫療證明", result["answer"])

    def test_index_is_valid_json(self) -> None:
        index = Path(__file__).resolve().parents[1] / "storage" / "index.json"
        payload = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertGreater(len(payload["chunks"]), 0)


if __name__ == "__main__":
    unittest.main()
