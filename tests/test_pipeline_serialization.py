from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.core.pipeline import PipelineSerializationError, load_pipeline_payload


class PipelineSerializationTests(unittest.TestCase):
    def test_rejects_corrupted_embedded_source_image(self) -> None:
        payload = {
            "format": "context.pipeline",
            "version": 1,
            "nodes": [
                {
                    "id": "source-1",
                    "type": "source",
                    "position": {"x": 10.0, "y": 20.0},
                    "params": {},
                    "state": {
                        "image_png_base64": "definitely-not-base64",
                        "image_name": "bad.png",
                    },
                },
                {
                    "id": "preview-1",
                    "type": "preview",
                    "position": {"x": 200.0, "y": 20.0},
                    "params": {},
                },
            ],
            "connections": [
                {
                    "source_node_id": "source-1",
                    "source_port": "image",
                    "target_node_id": "preview-1",
                    "target_port": "image",
                }
            ],
        }

        with self.assertRaises(PipelineSerializationError):
            load_pipeline_payload(payload)


if __name__ == "__main__":
    unittest.main()
