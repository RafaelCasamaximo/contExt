from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from context.localization import LocalizationController
from context.viewmodels import GraphViewModel
from context.views.canvas import GraphScene
from context.views.theme import ThemeController


class GraphSceneSnapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.graph_vm = GraphViewModel(bootstrap_default_graph=False, debounce_ms=0)
        self.source_vm = self.graph_vm.add_source_node((0.0, 0.0))
        self.blur_vm = self.graph_vm.add_blur_node((240.0, 0.0))
        self.preview_vm = self.graph_vm.add_preview_node((480.0, 0.0))
        assert self.source_vm is not None
        assert self.preview_vm is not None
        self.scene = GraphScene(
            self.graph_vm,
            ThemeController(initial_theme="material_dark"),
            LocalizationController(initial_locale="en"),
        )

    def test_find_snap_target_returns_nearest_compatible_input(self) -> None:
        source_item = self.scene.node_item(self.source_vm.node_id)
        blur_item = self.scene.node_item(self.blur_vm.node_id)
        assert source_item is not None
        assert blur_item is not None

        source_port = source_item.output_port("image")
        target_port = blur_item.input_port("image")
        probe_point = target_port.scene_center()
        probe_point.setX(probe_point.x() + 12.0)

        self.scene.begin_connection(source_port)
        try:
            self.assertIs(self.scene._find_snap_target(probe_point), target_port)
            self.scene._set_snap_target(target_port)
            self.assertIs(self.scene._snap_target_port, target_port)
        finally:
            self.scene._clear_temporary_edge()

    def test_find_snap_target_ignores_occupied_input(self) -> None:
        source_item = self.scene.node_item(self.source_vm.node_id)
        blur_item = self.scene.node_item(self.blur_vm.node_id)
        preview_item = self.scene.node_item(self.preview_vm.node_id)
        assert source_item is not None
        assert blur_item is not None
        assert preview_item is not None

        self.assertTrue(self.graph_vm.connect_nodes(self.source_vm.node_id, "image", self.blur_vm.node_id, "image"))

        preview_source = blur_item.output_port("image")
        occupied_target = blur_item.input_port("image")
        free_target = preview_item.input_port("image")

        occupied_probe = occupied_target.scene_center()
        occupied_probe.setX(occupied_probe.x() + 8.0)
        free_probe = free_target.scene_center()
        free_probe.setX(free_probe.x() + 8.0)

        self.scene.begin_connection(preview_source)
        try:
            self.assertIsNone(self.scene._find_snap_target(occupied_probe))
            self.assertIs(self.scene._find_snap_target(free_probe), free_target)
        finally:
            self.scene._clear_temporary_edge()


if __name__ == "__main__":
    unittest.main()
