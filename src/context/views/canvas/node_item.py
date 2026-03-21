from __future__ import annotations

from dataclasses import dataclass
import math

from PyQt6.QtCore import QRectF, QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGraphicsDropShadowEffect,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsProxyWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from context.core.nodes import NodeParamDefinition
from context.localization import LocalizationController
from context.viewmodels import GraphViewModel, NodeViewModel
from context.views.theme import ThemeController

from .port_item import PortItem


@dataclass(slots=True)
class _EmbeddedControl:
    definition: NodeParamDefinition
    label: QLabel | None = None
    slider: QSlider | None = None
    spin_box: QSpinBox | None = None
    double_spin_box: QDoubleSpinBox | None = None
    check_box: QCheckBox | None = None
    combo_box: QComboBox | None = None


class NodeItem(QGraphicsObject):
    geometryChanged = pyqtSignal(str)

    WIDTH = 236.0
    BASE_HEIGHT = 122.0
    TITLE_HEIGHT = 42.0
    CONTENT_TOP = 86.0
    CONTENT_X = 14.0
    CONTENT_WIDTH = int(WIDTH - (CONTENT_X * 2.0))
    BOTTOM_PADDING = 14.0
    FREQUENCY_PREVIEW_SIZE = (180, 112)

    def __init__(
        self,
        node_vm: NodeViewModel,
        graph_vm: GraphViewModel,
        theme_controller: ThemeController,
        localization_controller: LocalizationController,
    ) -> None:
        super().__init__()
        self.node_vm = node_vm
        self._graph_vm = graph_vm
        self._theme_controller = theme_controller
        self._localization = localization_controller
        self._has_result = False
        self._syncing_position = False
        self._input_ports: dict[str, PortItem] = {}
        self._output_ports: dict[str, PortItem] = {}
        self._definition = self._graph_vm.node_definition(self.node_vm.node_type)
        self._height = self.BASE_HEIGHT
        self._content_proxy: QGraphicsProxyWidget | None = None
        self._content_container: QWidget | None = None
        self._controls: dict[str, _EmbeddedControl] = {}
        self._frequency_preview_title: QLabel | None = None
        self._frequency_preview_label: QLabel | None = None
        self._frequency_preview_pixmap: QPixmap | None = None
        self._shadow = QGraphicsDropShadowEffect()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._shadow.setBlurRadius(28.0)
        self._shadow.setOffset(0.0, 10.0)
        self.setGraphicsEffect(self._shadow)
        self.setPos(*self.node_vm.position)
        self.node_vm.positionChanged.connect(self._sync_position_from_viewmodel)
        self.node_vm.updated.connect(self._handle_node_updated)
        self._theme_controller.themeChanged.connect(self._on_theme_changed)
        self._localization.localeChanged.connect(self._on_locale_changed)

        self._build_embedded_content()
        self._build_ports()
        self._apply_theme_to_shadow()
        self.refresh_from_model()

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.WIDTH, self._height)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # pragma: no cover - Qt paint path
        del option, widget
        theme = self._theme_controller.theme
        accent = QColor(self._accent_color())
        background = QColor(theme.surface)
        border = QColor(theme.selection if self.isSelected() else theme.border_soft)
        if self._has_result and not self.isSelected():
            border = accent

        painter.setPen(QPen(border, 2.0))
        painter.setBrush(background)
        painter.drawRoundedRect(self.boundingRect(), 14.0, 14.0)

        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(accent)
        painter.drawRoundedRect(QRectF(0.0, 0.0, self.WIDTH, self.TITLE_HEIGHT), 14.0, 14.0)
        painter.fillRect(
            QRectF(0.0, self.TITLE_HEIGHT / 2, self.WIDTH, self.TITLE_HEIGHT / 2),
            accent,
        )

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.drawText(
            QRectF(18.0, 0.0, self.WIDTH - 36.0, self.TITLE_HEIGHT),
            Qt.AlignmentFlag.AlignVCenter,
            self._tr(self._definition.title_key),
        )

        painter.setPen(QColor(theme.text_primary))
        body_font = QFont()
        body_font.setPointSize(9)
        painter.setFont(body_font)
        painter.drawText(
            QRectF(18.0, self.TITLE_HEIGHT + 16.0, self.WIDTH - 132.0, 18.0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._body_label(),
        )

        chip_rect = QRectF(self.WIDTH - 96.0, self.TITLE_HEIGHT + 12.0, 78.0, 22.0)
        chip_color = QColor(theme.surface_alt if not self._has_result else accent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(chip_color)
        painter.drawRoundedRect(chip_rect, 11.0, 11.0)
        painter.setPen(QColor(theme.text_inverse if self._has_result else theme.text_secondary))
        status_font = QFont()
        status_font.setPointSize(8)
        status_font.setBold(True)
        painter.setFont(status_font)
        painter.drawText(
            chip_rect,
            Qt.AlignmentFlag.AlignCenter,
            self._tr("node.status.ready" if self._has_result else "node.status.wait"),
        )

    def input_port(self, port_name: str) -> PortItem:
        return self._input_ports[port_name]

    def output_port(self, port_name: str) -> PortItem:
        return self._output_ports[port_name]

    def embedded_slider(self, param_key: str | None = None) -> QSlider | None:
        if param_key is not None:
            control = self._controls.get(param_key)
            return None if control is None else control.slider
        for control in self._controls.values():
            if control.slider is not None:
                return control.slider
        return None

    def embedded_spinbox(self, param_key: str) -> QSpinBox | None:
        control = self._controls.get(param_key)
        return None if control is None else control.spin_box

    def embedded_double_spinbox(self, param_key: str) -> QDoubleSpinBox | None:
        control = self._controls.get(param_key)
        return None if control is None else control.double_spin_box

    def embedded_checkbox(self, param_key: str) -> QCheckBox | None:
        control = self._controls.get(param_key)
        return None if control is None else control.check_box

    def embedded_combobox(self, param_key: str) -> QComboBox | None:
        control = self._controls.get(param_key)
        return None if control is None else control.combo_box

    def has_frequency_preview(self) -> bool:
        return self._frequency_preview_pixmap is not None

    @property
    def theme_name(self) -> str:
        return self._theme_controller.theme_name

    def set_result_state(self, has_result: bool) -> None:
        self._has_result = has_result
        self.update()

    def refresh_from_model(self) -> None:
        self._sync_embedded_controls()
        self._sync_frequency_preview()
        self._sync_frequency_control_states()
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if not self._syncing_position:
                self.node_vm.set_position(value.x(), value.y())
            self.geometryChanged.emit(self.node_vm.node_id)
        return super().itemChange(change, value)

    def _build_ports(self) -> None:
        node = self._graph_vm.get_node(self.node_vm.node_id)
        for port_name in node.input_ports:
            self._input_ports[port_name] = PortItem(self.node_vm.node_id, port_name, "input", self._theme_controller, self)
        for port_name in node.output_ports:
            self._output_ports[port_name] = PortItem(
                self.node_vm.node_id,
                port_name,
                "output",
                self._theme_controller,
                self,
            )
        self._layout_ports()

    def _layout_ports(self) -> None:
        if self._input_ports:
            step = self._height / (len(self._input_ports) + 1)
            for index, port_name in enumerate(self._input_ports, start=1):
                self._input_ports[port_name].setPos(0.0, step * index)
        if self._output_ports:
            step = self._height / (len(self._output_ports) + 1)
            for index, port_name in enumerate(self._output_ports, start=1):
                self._output_ports[port_name].setPos(self.WIDTH, step * index)

    def _build_embedded_content(self) -> None:
        has_controls = bool(self._definition.params) or self.node_vm.node_type == "frequency_domain_filter"
        if not has_controls:
            return

        container = QWidget()
        container.setFixedWidth(self.CONTENT_WIDTH)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for param_definition in self._definition.params:
            control_widget = self._build_param_control(param_definition)
            layout.addWidget(control_widget)

        if self.node_vm.node_type == "frequency_domain_filter":
            layout.addWidget(self._build_frequency_preview_card())

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(container)
        proxy.setPos(self.CONTENT_X, self.CONTENT_TOP)
        proxy.setZValue(1.0)

        self._content_container = container
        self._content_proxy = proxy
        self._update_height_from_content()

    def _build_param_control(self, param_definition: NodeParamDefinition) -> QWidget:
        card = QWidget()
        card.setObjectName("nodeControlCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        control = _EmbeddedControl(param_definition)
        self._controls[param_definition.key] = control

        if param_definition.kind in {"int", "float"}:
            top_row = QHBoxLayout()
            top_row.setContentsMargins(0, 0, 0, 0)
            top_row.setSpacing(8)

            label = QLabel()
            label.setObjectName("secondaryLabel")
            top_row.addWidget(label, 1)
            control.label = label

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setObjectName(f"nodeSlider-{param_definition.key}")
            control.slider = slider

            if param_definition.kind == "int":
                editor = QSpinBox()
                editor.setKeyboardTracking(False)
                control.spin_box = editor
                editor.valueChanged.connect(
                    lambda value, key=param_definition.key: self._on_numeric_editor_changed(key, value)
                )
            else:
                editor = QDoubleSpinBox()
                editor.setKeyboardTracking(False)
                editor.setDecimals(param_definition.decimals)
                control.double_spin_box = editor
                editor.valueChanged.connect(
                    lambda value, key=param_definition.key: self._on_numeric_editor_changed(key, value)
                )

            top_row.addWidget(editor, 0)
            slider.valueChanged.connect(
                lambda index, key=param_definition.key: self._on_numeric_slider_changed(key, index)
            )

            layout.addLayout(top_row)
            layout.addWidget(slider)
            return card

        if param_definition.kind == "bool":
            checkbox = QCheckBox()
            checkbox.toggled.connect(
                lambda checked, key=param_definition.key: self._graph_vm.set_node_param(self.node_vm.node_id, key, checked)
            )
            control.check_box = checkbox
            layout.addWidget(checkbox)
            return card

        if param_definition.kind == "enum":
            label = QLabel()
            label.setObjectName("secondaryLabel")
            control.label = label
            combo = QComboBox()
            combo.currentIndexChanged.connect(
                lambda _index, key=param_definition.key, combo_box=combo: self._graph_vm.set_node_param(
                    self.node_vm.node_id,
                    key,
                    combo_box.currentData(),
                )
            )
            control.combo_box = combo
            layout.addWidget(label)
            layout.addWidget(combo)
            return card

        fallback = QLabel(str(param_definition.default))
        fallback.setObjectName("secondaryLabel")
        layout.addWidget(fallback)
        return card

    def _build_frequency_preview_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("nodeControlCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel()
        title.setObjectName("secondaryLabel")
        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setMinimumSize(*self.FREQUENCY_PREVIEW_SIZE)
        preview.setMaximumSize(*self.FREQUENCY_PREVIEW_SIZE)
        preview.setStyleSheet("border-radius: 12px;")

        layout.addWidget(title)
        layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

        self._frequency_preview_title = title
        self._frequency_preview_label = preview
        return card

    def _sync_position_from_viewmodel(self, node_id: str, x: float, y: float) -> None:
        if node_id != self.node_vm.node_id:
            return
        if (self.x(), self.y()) == (x, y):
            return
        self._syncing_position = True
        self.setPos(x, y)
        self._syncing_position = False

    def _handle_node_updated(self, node_id: str) -> None:
        if node_id == self.node_vm.node_id:
            self.refresh_from_model()

    def _body_label(self) -> str:
        if self.node_vm.node_type == "source":
            node = self._graph_vm.get_node(self.node_vm.node_id)
            return self._tr("node.source.body.ready" if getattr(node, "image", None) is not None else "node.source.body.empty")
        return self._tr(self._definition.body_key)

    def _sync_embedded_controls(self) -> None:
        for param_definition in self._definition.params:
            control = self._controls.get(param_definition.key)
            if control is None:
                continue
            value = self.node_vm.params.get(param_definition.key, param_definition.default)
            if param_definition.kind in {"int", "float"}:
                self._sync_numeric_control(control, value)
            elif param_definition.kind == "bool" and control.check_box is not None:
                control.check_box.setText(self._tr(param_definition.label_key))
                blocker = QSignalBlocker(control.check_box)
                try:
                    control.check_box.setChecked(bool(value))
                finally:
                    del blocker
            elif param_definition.kind == "enum" and control.combo_box is not None:
                self._sync_combo_control(control, value)

    def _sync_numeric_control(self, control: _EmbeddedControl, value: object) -> None:
        minimum, maximum = self._param_bounds(control.definition)
        normalized = self._normalize_numeric_value(control.definition, value, minimum, maximum)
        step = self._numeric_step(control.definition)

        if control.label is not None:
            control.label.setText(self._tr(control.definition.label_key))
        if control.slider is not None:
            blocker = QSignalBlocker(control.slider)
            try:
                if control.definition.kind == "int":
                    slider_minimum = int(minimum)
                    slider_maximum = int(maximum)
                    control.slider.setMinimum(slider_minimum)
                    control.slider.setMaximum(slider_maximum)
                    control.slider.setSingleStep(int(step))
                    control.slider.setPageStep(max(int(step), max(1, (slider_maximum - slider_minimum) // 10)))
                    control.slider.setValue(int(normalized))
                else:
                    slider_steps = max(0, int(round((maximum - minimum) / step)))
                    slider_index = int(round((float(normalized) - minimum) / step))
                    control.slider.setMinimum(0)
                    control.slider.setMaximum(slider_steps)
                    control.slider.setSingleStep(1)
                    control.slider.setPageStep(max(1, slider_steps // 10))
                    control.slider.setValue(max(0, min(slider_steps, slider_index)))
            finally:
                del blocker
        if control.spin_box is not None:
            blocker = QSignalBlocker(control.spin_box)
            try:
                control.spin_box.setMinimum(int(minimum))
                control.spin_box.setMaximum(int(maximum))
                control.spin_box.setSingleStep(int(step))
                control.spin_box.setValue(int(normalized))
            finally:
                del blocker
        if control.double_spin_box is not None:
            blocker = QSignalBlocker(control.double_spin_box)
            try:
                control.double_spin_box.setMinimum(float(minimum))
                control.double_spin_box.setMaximum(float(maximum))
                control.double_spin_box.setSingleStep(float(step))
                control.double_spin_box.setValue(float(normalized))
            finally:
                del blocker

    def _sync_combo_control(self, control: _EmbeddedControl, value: object) -> None:
        combo_box = control.combo_box
        if combo_box is None:
            return
        if control.label is not None:
            control.label.setText(self._tr(control.definition.label_key))
        blocker = QSignalBlocker(combo_box)
        try:
            if combo_box.count() != len(control.definition.options):
                combo_box.clear()
                for option in control.definition.options:
                    combo_box.addItem(self._tr(option.label_key), option.value)
            else:
                for index, option in enumerate(control.definition.options):
                    combo_box.setItemText(index, self._tr(option.label_key))
            index = combo_box.findData(value)
            combo_box.setCurrentIndex(index if index >= 0 else 0)
        finally:
            del blocker

    def _sync_frequency_preview(self) -> None:
        if self._frequency_preview_title is None or self._frequency_preview_label is None:
            return

        self._frequency_preview_title.setText(self._tr("node.frequency_domain_filter.preview"))
        image = self._graph_vm.node_visual(self.node_vm.node_id, "frequency_spectrum")
        if image is None:
            self._frequency_preview_pixmap = None
            self._frequency_preview_label.setPixmap(QPixmap())
            self._frequency_preview_label.setText(self._tr("node.frequency_domain_filter.preview.unavailable"))
            return

        display_image = image.copy()
        height, width, channels = display_image.shape
        bytes_per_line = channels * width
        qimage = QImage(
            display_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        pixmap = QPixmap.fromImage(qimage)
        self._frequency_preview_pixmap = pixmap
        self._frequency_preview_label.setText("")
        self._frequency_preview_label.setPixmap(
            pixmap.scaled(
                self.FREQUENCY_PREVIEW_SIZE[0],
                self.FREQUENCY_PREVIEW_SIZE[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _sync_frequency_control_states(self) -> None:
        if self.node_vm.node_type != "frequency_domain_filter":
            return
        mode = str(self.node_vm.params.get("mode", "none"))
        cutoff_enabled = mode in {"low_pass", "high_pass"}
        band_enabled = mode in {"band_pass", "band_stop"}

        for key, enabled in {
            "cutoff": cutoff_enabled,
            "band_min": band_enabled,
            "band_max": band_enabled,
        }.items():
            control = self._controls.get(key)
            if control is None:
                continue
            for widget in (control.label, control.slider, control.spin_box, control.double_spin_box):
                if widget is not None:
                    widget.setEnabled(enabled)

    def _on_numeric_editor_changed(self, key: str, value: int | float) -> None:
        control = self._controls[key]
        minimum, maximum = self._param_bounds(control.definition)
        normalized = self._normalize_numeric_value(control.definition, value, minimum, maximum)
        self._sync_numeric_control(control, normalized)
        self._graph_vm.set_node_param(self.node_vm.node_id, key, normalized)

    def _on_numeric_slider_changed(self, key: str, index: int) -> None:
        control = self._controls[key]
        minimum, maximum = self._param_bounds(control.definition)
        if control.definition.kind == "int":
            value = index
        else:
            step = self._numeric_step(control.definition)
            value = minimum + (index * step)
        normalized = self._normalize_numeric_value(control.definition, value, minimum, maximum)
        self._sync_numeric_control(control, normalized)
        self._graph_vm.set_node_param(self.node_vm.node_id, key, normalized)

    def _param_bounds(self, definition: NodeParamDefinition) -> tuple[float, float]:
        minimum = float(definition.minimum if definition.minimum is not None else 0.0)
        maximum = float(definition.maximum if definition.maximum is not None else minimum)
        input_image = self._graph_vm.node_input_image(self.node_vm.node_id)

        if input_image is not None and self.node_vm.node_type == "crop":
            height, width = input_image.shape[:2]
            if definition.key in {"start_x", "end_x"}:
                maximum = max(minimum, float(width))
            elif definition.key in {"start_y", "end_y"}:
                maximum = max(minimum, float(height))

        if input_image is not None and self.node_vm.node_type == "frequency_domain_filter":
            if definition.key in {"cutoff", "band_min", "band_max"}:
                height, width = input_image.shape[:2]
                maximum = max(minimum, float(max(1, math.ceil(math.hypot(height / 2.0, width / 2.0)))))

        if definition.kind == "int" and definition.odd_only:
            minimum = float(int(minimum) if int(minimum) % 2 == 1 else int(minimum) + 1)
            maximum_int = int(maximum)
            if maximum_int % 2 == 0:
                maximum_int -= 1
            if maximum_int < int(minimum):
                maximum_int = int(minimum)
            maximum = float(maximum_int)

        return minimum, maximum

    @staticmethod
    def _numeric_step(definition: NodeParamDefinition) -> float:
        step = float(definition.step or 1.0)
        if definition.kind == "int" and definition.odd_only:
            return max(2.0, step)
        return step

    def _normalize_numeric_value(
        self,
        definition: NodeParamDefinition,
        value: object,
        minimum: float,
        maximum: float,
    ) -> int | float:
        step = self._numeric_step(definition)
        coerced = float(value)
        coerced = max(minimum, min(maximum, coerced))
        snapped = minimum + round((coerced - minimum) / step) * step
        snapped = max(minimum, min(maximum, snapped))

        if definition.kind == "int":
            normalized = int(round(snapped))
            if definition.odd_only and normalized % 2 == 0:
                normalized = normalized + 1 if normalized < int(maximum) else normalized - 1
            return max(int(minimum), min(int(maximum), normalized))

        return round(snapped, definition.decimals)

    def _update_height_from_content(self) -> None:
        if self._content_container is None:
            return
        self._content_container.adjustSize()
        content_height = float(self._content_container.sizeHint().height())
        new_height = max(self.BASE_HEIGHT, self.CONTENT_TOP + content_height + self.BOTTOM_PADDING)
        if math.isclose(new_height, self._height):
            return
        self.prepareGeometryChange()
        self._height = new_height
        self._layout_ports()
        if self.scene() is not None:
            self.geometryChanged.emit(self.node_vm.node_id)

    def _on_theme_changed(self, _theme) -> None:
        self._apply_theme_to_shadow()
        self.update()

    def _on_locale_changed(self, _locale_code: str) -> None:
        for control in self._controls.values():
            if control.definition.kind == "bool" and control.check_box is not None:
                control.check_box.setText(self._tr(control.definition.label_key))
        self.refresh_from_model()
        self._update_height_from_content()

    def _apply_theme_to_shadow(self) -> None:
        self._shadow.setColor(QColor(self._theme_controller.theme.shadow))

    def _tr(self, key: str, **kwargs) -> str:
        return self._localization.tr(key, **kwargs)

    def _accent_color(self) -> str:
        theme = self._theme_controller.theme
        category = self._definition.category
        if category == "input":
            return theme.source_accent
        if category == "filtering":
            return theme.blur_accent
        if category in {"frequency", "output"}:
            return theme.preview_accent
        if category == "thresholding":
            return theme.selection
        return theme.source_accent
