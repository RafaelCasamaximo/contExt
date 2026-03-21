from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFormLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from context.core.nodes import SourceNode
from context.localization import LocalizationController
from context.viewmodels import GraphViewModel, NodeViewModel


class PropertiesPanel(QWidget):
    def __init__(
        self,
        graph_vm: GraphViewModel,
        localization_controller: LocalizationController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._graph_vm = graph_vm
        self._localization = localization_controller
        self._selected_node_id: str | None = None

        self._title_label = QLabel("No node selected")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._description_label = QLabel("Select a node to edit its properties.")
        self._description_label.setObjectName("secondaryLabel")
        self._description_label.setWordWrap(True)
        self._form = QFormLayout()
        self._form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self._title_label)
        layout.addWidget(self._description_label)
        layout.addLayout(self._form)
        layout.addStretch(1)

        self._graph_vm.selectedNodeChanged.connect(self._on_selected_node_changed)
        self._graph_vm.nodeChanged.connect(self._on_node_changed)
        self._localization.localeChanged.connect(self._on_locale_changed)

    def _on_selected_node_changed(self, node_vm: NodeViewModel | None) -> None:
        self._selected_node_id = None if node_vm is None else node_vm.node_id
        self._render_selected_node(node_vm)

    def _on_node_changed(self, node_id: str) -> None:
        if node_id == self._selected_node_id:
            self._render_selected_node(self._graph_vm.node_viewmodels[node_id])

    def _render_selected_node(self, node_vm: NodeViewModel | None) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)

        if node_vm is None:
            self._title_label.setText(self._localization.tr("panel.none.title"))
            self._description_label.setText(self._localization.tr("panel.none.description"))
            return

        node = self._graph_vm.get_node(node_vm.node_id)
        self._title_label.setText(self._localization.tr(f"node.{node_vm.node_type}.title"))

        if node_vm.node_type == "source" and isinstance(node, SourceNode):
            self._description_label.setText(self._localization.tr("panel.source.description"))
            self._form.addRow(self._localization.tr("panel.source.path"), QLabel(node.image_path or self._localization.tr("panel.source.no_image")))
            resolution = self._localization.tr("panel.source.no_image")
            if node.image is not None:
                resolution = f"{node.image.shape[1]} x {node.image.shape[0]}"
            self._form.addRow(self._localization.tr("panel.source.resolution"), QLabel(resolution))
            return

        if node_vm.node_type == "blur":
            self._description_label.setText(self._localization.tr("panel.blur.description"))
            kernel_input = QSpinBox()
            kernel_input.setRange(1, 31)
            kernel_input.setSingleStep(2)
            kernel_input.setValue(int(node_vm.params.get("kernel_size", 5)))
            kernel_input.valueChanged.connect(
                lambda value, node_id=node_vm.node_id: self._graph_vm.set_node_param(node_id, "kernel_size", value)
            )
            self._form.addRow(self._localization.tr("panel.blur.kernel_size"), kernel_input)
            return

        if node_vm.node_type == "preview":
            self._description_label.setText(self._localization.tr("panel.preview.description"))
            status = self._localization.tr(
                "panel.preview.ready" if self._graph_vm.current_preview() is not None else "panel.preview.waiting"
            )
            self._form.addRow(self._localization.tr("panel.preview.status"), QLabel(status))
            return

        self._description_label.setText(self._localization.tr("panel.none.description"))

    def _on_locale_changed(self, _locale_code: str) -> None:
        if self._selected_node_id is None:
            self._render_selected_node(None)
            return
        self._render_selected_node(self._graph_vm.node_viewmodels[self._selected_node_id])
