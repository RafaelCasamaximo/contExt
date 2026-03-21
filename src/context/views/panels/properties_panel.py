from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from context.core.nodes import NodeParamDefinition, SourceNode
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
        self._param_widgets: dict[str, QWidget] = {}

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
        self._graph_vm.previewUpdated.connect(self._on_preview_updated)
        self._localization.localeChanged.connect(self._on_locale_changed)

    def _on_selected_node_changed(self, node_vm: NodeViewModel | None) -> None:
        self._selected_node_id = None if node_vm is None else node_vm.node_id
        self._render_selected_node(node_vm)

    def _on_node_changed(self, node_id: str) -> None:
        if node_id == self._selected_node_id:
            node_vm = self._graph_vm.node_viewmodels[node_id]
            if node_vm.node_type in {"source", "preview"} or not self._param_widgets:
                self._render_selected_node(node_vm)
                return
            self._sync_param_widgets(node_vm)

    def _render_selected_node(self, node_vm: NodeViewModel | None) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)
        self._param_widgets = {}

        if node_vm is None:
            self._title_label.setText(self._localization.tr("panel.none.title"))
            self._description_label.setText(self._localization.tr("panel.none.description"))
            return

        node = self._graph_vm.get_node(node_vm.node_id)
        definition = self._graph_vm.node_definition(node_vm.node_type)
        self._title_label.setText(self._localization.tr(definition.title_key))

        if node_vm.node_type == "source" and isinstance(node, SourceNode):
            self._description_label.setText(self._localization.tr("panel.source.description"))
            self._form.addRow(self._localization.tr("panel.source.path"), QLabel(node.image_path or self._localization.tr("panel.source.no_image")))
            resolution = self._localization.tr("panel.source.no_image")
            if node.image is not None:
                resolution = f"{node.image.shape[1]} x {node.image.shape[0]}"
            self._form.addRow(self._localization.tr("panel.source.resolution"), QLabel(resolution))
            return

        if node_vm.node_type == "preview":
            self._description_label.setText(self._localization.tr("panel.preview.description"))
            status = self._localization.tr(
                "panel.preview.ready" if self._graph_vm.current_preview() is not None else "panel.preview.waiting"
            )
            self._form.addRow(self._localization.tr("panel.preview.status"), QLabel(status))
            return

        self._description_label.setText(self._localization.tr(definition.description_key))
        for param_definition in definition.params:
            widget = self._build_param_widget(node_vm, param_definition)
            self._param_widgets[param_definition.key] = widget
            self._form.addRow(self._localization.tr(param_definition.label_key), widget)

    def _on_locale_changed(self, _locale_code: str) -> None:
        if self._selected_node_id is None:
            self._render_selected_node(None)
            return
        self._render_selected_node(self._graph_vm.node_viewmodels[self._selected_node_id])

    def _build_param_widget(self, node_vm: NodeViewModel, param_definition: NodeParamDefinition):
        value = node_vm.params.get(param_definition.key, param_definition.default)
        if param_definition.kind == "int":
            widget = QSpinBox()
            if param_definition.minimum is not None:
                widget.setMinimum(int(param_definition.minimum))
            if param_definition.maximum is not None:
                widget.setMaximum(int(param_definition.maximum))
            step = int(param_definition.step or 1)
            if param_definition.odd_only:
                step = max(2, step)
            widget.setSingleStep(step)
            widget.setValue(int(value))
            widget.valueChanged.connect(
                lambda new_value, node_id=node_vm.node_id, key=param_definition.key: self._graph_vm.set_node_param(node_id, key, new_value)
            )
            return widget

        if param_definition.kind == "float":
            widget = QDoubleSpinBox()
            widget.setDecimals(param_definition.decimals)
            if param_definition.minimum is not None:
                widget.setMinimum(float(param_definition.minimum))
            if param_definition.maximum is not None:
                widget.setMaximum(float(param_definition.maximum))
            if param_definition.step is not None:
                widget.setSingleStep(float(param_definition.step))
            widget.setValue(float(value))
            widget.valueChanged.connect(
                lambda new_value, node_id=node_vm.node_id, key=param_definition.key: self._graph_vm.set_node_param(node_id, key, new_value)
            )
            return widget

        if param_definition.kind == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.toggled.connect(
                lambda checked, node_id=node_vm.node_id, key=param_definition.key: self._graph_vm.set_node_param(node_id, key, checked)
            )
            return widget

        if param_definition.kind == "enum":
            widget = QComboBox()
            for option in param_definition.options:
                widget.addItem(self._localization.tr(option.label_key), option.value)
            current_index = widget.findData(value)
            if current_index >= 0:
                widget.setCurrentIndex(current_index)
            widget.currentIndexChanged.connect(
                lambda _index, combo=widget, node_id=node_vm.node_id, key=param_definition.key: self._graph_vm.set_node_param(node_id, key, combo.currentData())
            )
            return widget

        return QLabel(str(value))

    def _sync_param_widgets(self, node_vm: NodeViewModel) -> None:
        definition = self._graph_vm.node_definition(node_vm.node_type)
        for param_definition in definition.params:
            widget = self._param_widgets.get(param_definition.key)
            if widget is None:
                continue
            value = node_vm.params.get(param_definition.key, param_definition.default)
            blocker = QSignalBlocker(widget)
            try:
                if isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findData(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
            finally:
                del blocker

    def _on_preview_updated(self, _image) -> None:
        if self._selected_node_id is None:
            return
        node_vm = self._graph_vm.node_viewmodels.get(self._selected_node_id)
        if node_vm is not None and node_vm.node_type == "preview":
            self._render_selected_node(node_vm)
