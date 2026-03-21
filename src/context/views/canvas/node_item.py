from __future__ import annotations

from PyQt6.QtCore import QRectF, QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsProxyWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from context.viewmodels import GraphViewModel, NodeViewModel
from context.views.theme import ThemeController

from .port_item import PortItem


class NodeItem(QGraphicsObject):
    geometryChanged = pyqtSignal(str)

    WIDTH = 220.0
    BASE_HEIGHT = 122.0
    BLUR_HEIGHT = 176.0
    TITLE_HEIGHT = 42.0

    def __init__(self, node_vm: NodeViewModel, graph_vm: GraphViewModel, theme_controller: ThemeController) -> None:
        super().__init__()
        self.node_vm = node_vm
        self._graph_vm = graph_vm
        self._theme_controller = theme_controller
        self._has_result = False
        self._syncing_position = False
        self._input_ports: dict[str, PortItem] = {}
        self._output_ports: dict[str, PortItem] = {}
        self._height = self.BLUR_HEIGHT if self.node_vm.node_type == "blur" else self.BASE_HEIGHT
        self._slider_proxy: QGraphicsProxyWidget | None = None
        self._kernel_slider: QSlider | None = None
        self._kernel_value_label: QLabel | None = None
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

        self._build_ports()
        self._build_embedded_controls()
        self._apply_theme_to_shadow()

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.WIDTH, self._height)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # pragma: no cover - Qt paint path
        del option, widget
        theme = self._theme_controller.theme
        accent = QColor(theme.accent_for_node(self.node_vm.node_type))
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
            self.node_vm.title,
        )

        painter.setPen(QColor(theme.text_primary))
        body_font = QFont()
        body_font.setPointSize(9)
        painter.setFont(body_font)
        painter.drawText(
            QRectF(18.0, self.TITLE_HEIGHT + 16.0, self.WIDTH - 36.0, 18.0),
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
        painter.drawText(chip_rect, Qt.AlignmentFlag.AlignCenter, "READY" if self._has_result else "WAIT")

    def input_port(self, port_name: str) -> PortItem:
        return self._input_ports[port_name]

    def output_port(self, port_name: str) -> PortItem:
        return self._output_ports[port_name]

    def embedded_slider(self) -> QSlider | None:
        return self._kernel_slider

    @property
    def theme_name(self) -> str:
        return self._theme_controller.theme_name

    def set_result_state(self, has_result: bool) -> None:
        self._has_result = has_result
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if not self._syncing_position:
                self.node_vm.set_position(value.x(), value.y())
            self.geometryChanged.emit(self.node_vm.node_id)
        return super().itemChange(change, value)

    def _build_ports(self) -> None:
        node = self._graph_vm.get_node(self.node_vm.node_id)
        if node.input_ports:
            step = self._height / (len(node.input_ports) + 1)
            for index, port_name in enumerate(node.input_ports, start=1):
                port_item = PortItem(self.node_vm.node_id, port_name, "input", self._theme_controller, self)
                port_item.setPos(0.0, step * index)
                self._input_ports[port_name] = port_item
        if node.output_ports:
            step = self._height / (len(node.output_ports) + 1)
            for index, port_name in enumerate(node.output_ports, start=1):
                port_item = PortItem(self.node_vm.node_id, port_name, "output", self._theme_controller, self)
                port_item.setPos(self.WIDTH, step * index)
                self._output_ports[port_name] = port_item

    def _build_embedded_controls(self) -> None:
        if self.node_vm.node_type != "blur":
            return

        container = QWidget()
        container.setObjectName("nodeControlCard")
        container.setFixedWidth(int(self.WIDTH - 28.0))

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Kernel")
        label.setObjectName("secondaryLabel")
        value_label = QLabel()
        value_label.setObjectName("nodeChipLabel")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(1, 31)
        slider.setSingleStep(2)
        slider.setPageStep(2)
        slider.setTickInterval(2)
        slider.valueChanged.connect(self._on_kernel_slider_changed)

        top_row.addWidget(label)
        top_row.addStretch(1)
        top_row.addWidget(value_label)

        layout.addLayout(top_row)
        layout.addWidget(slider)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(container)
        proxy.setPos(14.0, 88.0)
        proxy.setZValue(1.0)

        self._slider_proxy = proxy
        self._kernel_slider = slider
        self._kernel_value_label = value_label
        self._sync_embedded_controls()

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
            self._sync_embedded_controls()
            self.update()

    def _body_label(self) -> str:
        if self.node_vm.node_type == "source":
            node = self._graph_vm.get_node(self.node_vm.node_id)
            return "Image ready" if getattr(node, "image", None) is not None else "Load an image"
        if self.node_vm.node_type == "blur":
            return "Gaussian blur"
        return "Canvas output"

    def _sync_embedded_controls(self) -> None:
        if self._kernel_slider is None or self._kernel_value_label is None:
            return
        kernel_size = int(self.node_vm.params.get("kernel_size", 5))
        with QSignalBlocker(self._kernel_slider):
            self._kernel_slider.setValue(kernel_size)
        self._kernel_value_label.setText(str(kernel_size))

    def _on_kernel_slider_changed(self, value: int) -> None:
        if value % 2 == 0:
            value = value + 1 if value < 31 else value - 1
            if self._kernel_slider is not None:
                with QSignalBlocker(self._kernel_slider):
                    self._kernel_slider.setValue(value)
        if self._kernel_value_label is not None:
            self._kernel_value_label.setText(str(value))
        self._graph_vm.set_node_param(self.node_vm.node_id, "kernel_size", value)

    def _on_theme_changed(self, _theme) -> None:
        self._apply_theme_to_shadow()
        self.update()

    def _apply_theme_to_shadow(self) -> None:
        self._shadow.setColor(QColor(self._theme_controller.theme.shadow))
