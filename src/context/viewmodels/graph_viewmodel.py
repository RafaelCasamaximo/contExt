from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
from typing import Any

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, pyqtSignal

from context.core.nodes import (
    SourceNode,
    available_node_definitions,
    create_node as create_registered_node,
    get_node_definition,
    grouped_menu_definitions,
)
from context.localization import LocalizationController, translate
from context.core.pipeline import (
    Connection,
    ExecutionResult,
    Executor,
    Graph,
    ImageArray,
    PipelineSerializationError,
    export_pipeline_payload,
    load_pipeline_payload,
    read_pipeline_file,
    write_pipeline_file,
)
from context.viewmodels.node_viewmodel import NodeViewModel


class _ExecutionSignals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(int, str)


class _ExecutionRunnable(QRunnable):
    def __init__(
        self,
        generation: int,
        graph_snapshot: Graph,
        cached_results: dict[str, np.ndarray | None],
        cached_visuals: dict[str, dict[str, np.ndarray | None]],
        invalidated: set[str],
    ) -> None:
        super().__init__()
        self._generation = generation
        self._graph_snapshot = graph_snapshot
        self._cached_results = cached_results
        self._cached_visuals = cached_visuals
        self._invalidated = invalidated
        self.signals = _ExecutionSignals()

    def run(self) -> None:
        try:
            result = Executor.execute(
                self._graph_snapshot,
                self._cached_results,
                self._invalidated,
                generation=self._generation,
                cached_visuals=self._cached_visuals,
            )
        except Exception as exc:  # pragma: no cover - emitted to the UI layer
            self.signals.failed.emit(self._generation, str(exc))
            return
        self.signals.finished.emit(result)


class GraphViewModel(QObject):
    nodeAdded = pyqtSignal(object)
    nodeRemoved = pyqtSignal(str)
    nodeChanged = pyqtSignal(str)
    connectionAdded = pyqtSignal(object)
    connectionRemoved = pyqtSignal(object)
    selectedNodeChanged = pyqtSignal(object)
    nodeResultUpdated = pyqtSignal(str, object)
    previewUpdated = pyqtSignal(object)
    processingChanged = pyqtSignal(bool)
    errorRaised = pyqtSignal(str)
    imageLoaded = pyqtSignal(str)

    def __init__(
        self,
        localization_controller: LocalizationController | None = None,
        bootstrap_default_graph: bool = True,
        debounce_ms: int = 120,
    ) -> None:
        super().__init__()
        self._localization = localization_controller
        self.graph = Graph()
        self.node_viewmodels: dict[str, NodeViewModel] = {}
        self._node_counters: defaultdict[str, int] = defaultdict(int)
        self._results: dict[str, np.ndarray | None] = {}
        self._node_visuals: dict[str, dict[str, np.ndarray | None]] = {}
        self._selected_node_id: str | None = None
        self._pending_invalidated: set[str] = set()
        self._active_generations: set[int] = set()
        self._latest_requested_generation = 0
        self._latest_completed_generation = 0
        self._source_node_id: str | None = None
        self._preview_node_id: str | None = None

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(debounce_ms)
        self._debounce_timer.timeout.connect(self._dispatch_pending_execution)

        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(max(2, min(4, QThread.idealThreadCount())))

        if bootstrap_default_graph:
            self.add_source_node((60.0, 120.0))
            self.add_preview_node((420.0, 120.0))

    def create_node(
        self,
        node_type: str,
        position: tuple[float, float],
        node_id: str | None = None,
        params: dict[str, object] | None = None,
    ) -> NodeViewModel:
        resolved_node_id = node_id or self._next_node_id(node_type)
        node = create_registered_node(node_type, resolved_node_id, params)
        self._sync_counter_from_id(node_type, resolved_node_id)
        self.graph.add_node(node)

        node_vm = NodeViewModel(node, *position)
        node_vm.positionChanged.connect(self._on_node_position_changed)
        self.node_viewmodels[resolved_node_id] = node_vm

        definition = get_node_definition(node_type)
        if definition.singleton and node_type == "source":
            self._source_node_id = resolved_node_id
        elif definition.singleton and node_type == "preview":
            self._preview_node_id = resolved_node_id

        self.nodeAdded.emit(node_vm)
        self.nodeChanged.emit(resolved_node_id)
        return node_vm

    def add_source_node(self, position: tuple[float, float]) -> NodeViewModel | None:
        if self.graph.find_node_by_type("source") is not None:
            self.errorRaised.emit(self._tr("graph.error.only_one_source"))
            return None
        return self.create_node("source", position)

    def add_blur_node(self, position: tuple[float, float]) -> NodeViewModel:
        return self.create_node("blur", position)

    def add_preview_node(self, position: tuple[float, float]) -> NodeViewModel | None:
        if self.graph.find_node_by_type("preview") is not None:
            self.errorRaised.emit(self._tr("graph.error.only_one_preview"))
            return None
        return self.create_node("preview", position)

    def add_node(self, node_type: str, position: tuple[float, float]) -> NodeViewModel | None:
        if node_type == "source":
            return self.add_source_node(position)
        if node_type == "preview":
            return self.add_preview_node(position)
        try:
            definition = get_node_definition(node_type)
        except ValueError:
            self.errorRaised.emit(self._tr("graph.error.unsupported_node_type", type_name=node_type))
            return None

        if definition.singleton and self.graph.find_node_by_type(node_type) is not None:
            if node_type == "source":
                self.errorRaised.emit(self._tr("graph.error.only_one_source"))
            elif node_type == "preview":
                self.errorRaised.emit(self._tr("graph.error.only_one_preview"))
            else:
                self.errorRaised.emit(self._tr("graph.error.only_one_singleton", title=self._tr(definition.title_key)))
            return None
        return self.create_node(node_type, position)

    def remove_node(self, node_id: str) -> None:
        node = self.graph.nodes.get(node_id)
        if node is None:
            return

        removed_connections = self.graph.remove_node(node_id)
        self.node_viewmodels.pop(node_id, None)
        self._results.pop(node_id, None)
        self._node_visuals.pop(node_id, None)

        if node.type_name == "source":
            self._source_node_id = None
        elif node.type_name == "preview":
            self._preview_node_id = None
            self.previewUpdated.emit(None)

        for connection in removed_connections:
            self.connectionRemoved.emit(connection)

        if self._selected_node_id == node_id:
            self._selected_node_id = None
            self.selectedNodeChanged.emit(None)

        impacted = {connection.target_node_id for connection in removed_connections if connection.target_node_id in self.graph.nodes}
        if impacted:
            self.schedule_reprocess(impacted)
        self.nodeRemoved.emit(node_id)

    def connect_nodes(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> bool:
        try:
            connection = self.graph.connect(source_node_id, source_port, target_node_id, target_port)
        except (KeyError, ValueError) as exc:
            self.errorRaised.emit(self._localize_connection_error(str(exc)))
            return False
        self.connectionAdded.emit(connection)
        self.schedule_reprocess({target_node_id})
        return True

    def disconnect_nodes(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> None:
        try:
            self.graph.disconnect(source_node_id, source_port, target_node_id, target_port)
        except KeyError:
            return
        connection = Connection(source_node_id, source_port, target_node_id, target_port)
        self.connectionRemoved.emit(connection)
        self.schedule_reprocess({target_node_id})

    def get_node(self, node_id: str):
        return self.graph.nodes[node_id]

    def set_selected_node(self, node_id: str | None) -> None:
        if self._selected_node_id == node_id:
            return
        self._selected_node_id = node_id
        self.selectedNodeChanged.emit(None if node_id is None else self.node_viewmodels[node_id])

    def set_node_param(self, node_id: str, key: str, value: Any) -> None:
        node = self.graph.nodes[node_id]
        previous_value = node.params.get(key)
        node.set_param(key, value)
        current_value = node.params.get(key)
        if current_value == previous_value:
            return
        self.node_viewmodels[node_id].sync_from_node(node)
        self.nodeChanged.emit(node_id)
        self.schedule_reprocess({node_id})

    def set_source_image(self, image: np.ndarray, image_path: str | None = None) -> None:
        source_node = self._get_or_create_source()
        source_node.set_image(image, image_path)
        self.node_viewmodels[source_node.id].sync_from_node(source_node)
        self.nodeChanged.emit(source_node.id)
        if image_path:
            self.imageLoaded.emit(image_path)
        self.schedule_reprocess({source_node.id})

    def load_image(self, file_path: str) -> None:
        image_path = Path(file_path)
        with Image.open(image_path) as image:
            rgb = image.convert("RGB")
            array = np.array(rgb, dtype=np.uint8)
        self.set_source_image(array, str(image_path))

    def list_nodes(self) -> list[NodeViewModel]:
        return list(self.node_viewmodels.values())

    def current_preview(self) -> np.ndarray | None:
        if self._preview_node_id is None:
            return None
        return self._results.get(self._preview_node_id)

    def node_visual(self, node_id: str, key: str) -> np.ndarray | None:
        visuals = self._node_visuals.get(node_id)
        if visuals is None:
            return None
        image = visuals.get(key)
        if image is None:
            return None
        return image.copy()

    def node_input_image(self, node_id: str, port_name: str = "image") -> ImageArray | None:
        connection = self.graph.get_input_connection(node_id, port_name)
        if connection is None:
            return None
        return self._results.get(connection.source_node_id)

    def node_definition(self, node_type: str):
        return get_node_definition(node_type)

    def available_node_definitions(self, *, menu_only: bool = False):
        return available_node_definitions(menu_only=menu_only)

    def grouped_menu_definitions(self):
        return grouped_menu_definitions()

    def export_pipeline_payload(self) -> dict[str, object]:
        positions = {
            node_id: node_vm.position
            for node_id, node_vm in self.node_viewmodels.items()
        }
        return export_pipeline_payload(self.graph, positions)

    def save_pipeline(self, file_path: str) -> bool:
        try:
            write_pipeline_file(
                file_path,
                self.graph,
                {node_id: node_vm.position for node_id, node_vm in self.node_viewmodels.items()},
            )
        except PipelineSerializationError as exc:
            self.errorRaised.emit(self._tr("graph.error.pipeline_save_failed", message=str(exc)))
            return False
        return True

    def load_pipeline(self, file_path: str) -> bool:
        try:
            document = read_pipeline_file(file_path)
        except PipelineSerializationError as exc:
            self.errorRaised.emit(self._tr("graph.error.pipeline_load_failed", message=str(exc)))
            return False
        self._apply_loaded_pipeline(document)
        return True

    def load_pipeline_payload(self, payload: object) -> bool:
        try:
            document = load_pipeline_payload(payload)
        except PipelineSerializationError as exc:
            self.errorRaised.emit(self._tr("graph.error.pipeline_load_failed", message=str(exc)))
            return False
        self._apply_loaded_pipeline(document)
        return True

    def schedule_reprocess(self, invalidated: set[str]) -> None:
        self._pending_invalidated.update(node_id for node_id in invalidated if node_id in self.graph.nodes)
        if not self._pending_invalidated:
            return
        self._debounce_timer.start()

    def force_reprocess(self, invalidated: set[str]) -> None:
        self._pending_invalidated.update(node_id for node_id in invalidated if node_id in self.graph.nodes)
        self._dispatch_pending_execution()

    def _dispatch_pending_execution(self) -> None:
        if not self._pending_invalidated:
            return

        invalidated = set(self._pending_invalidated)
        self._pending_invalidated.clear()

        self._latest_requested_generation += 1
        generation = self._latest_requested_generation
        runnable = _ExecutionRunnable(
            generation,
            self.graph.clone(),
            dict(self._results),
            {node_id: dict(visuals) for node_id, visuals in self._node_visuals.items()},
            invalidated,
        )
        runnable.signals.finished.connect(self._on_execution_finished)
        runnable.signals.failed.connect(self._on_execution_failed)

        if not self._active_generations:
            self.processingChanged.emit(True)
        self._active_generations.add(generation)
        self._thread_pool.start(runnable)

    def _on_execution_finished(self, result: ExecutionResult) -> None:
        self._active_generations.discard(result.generation)
        if result.generation >= self._latest_requested_generation and result.generation >= self._latest_completed_generation:
            self._latest_completed_generation = result.generation
            self._results = result.results
            self._node_visuals = result.visuals
            for node_id in result.impacted_order:
                self.nodeResultUpdated.emit(node_id, self._results.get(node_id))
            preview_node_id = self._preview_node_id
            preview = None if preview_node_id is None else self._results.get(preview_node_id)
            self.previewUpdated.emit(preview)

        if not self._active_generations:
            self.processingChanged.emit(False)

    def _on_execution_failed(self, generation: int, message: str) -> None:
        self._active_generations.discard(generation)
        self.errorRaised.emit(message)
        if not self._active_generations:
            self.processingChanged.emit(False)

    def _on_node_position_changed(self, node_id: str, x: float, y: float) -> None:
        del node_id, x, y

    def _next_node_id(self, node_type: str) -> str:
        self._node_counters[node_type] += 1
        return f"{node_type}-{self._node_counters[node_type]}"

    def _get_or_create_source(self) -> SourceNode:
        if self._source_node_id is None:
            node_vm = self.add_source_node((60.0, 120.0))
            if node_vm is None:
                raise RuntimeError("Could not create Source node.")
            self._source_node_id = node_vm.node_id
        source_node = self.graph.nodes[self._source_node_id]
        if not isinstance(source_node, SourceNode):
            raise TypeError("Source node has an invalid type.")
        return source_node

    def _tr(self, key: str, **kwargs) -> str:
        if self._localization is not None:
            return self._localization.tr(key, **kwargs)
        return translate("en", key, **kwargs)

    def _localize_connection_error(self, raw_message: str) -> str:
        if raw_message == "Self connections are not allowed.":
            return self._tr("graph.error.connection_self")
        if raw_message == "Connection would create a cycle.":
            return self._tr("graph.error.connection_cycle")
        if "already has a connection" in raw_message:
            return self._tr("graph.error.connection_input_occupied")
        if raw_message.startswith("Unknown node"):
            return self._tr("graph.error.connection_unknown_node")
        if "has no input port" in raw_message or "has no output port" in raw_message:
            return self._tr("graph.error.connection_invalid_port")
        return self._tr("graph.error.connection_rejected")

    def _apply_loaded_pipeline(self, document) -> None:
        self._clear_graph_state()

        for loaded_node in document.nodes:
            node = loaded_node.node.clone()
            node_vm = NodeViewModel(node, *loaded_node.position)
            node_vm.positionChanged.connect(self._on_node_position_changed)
            self.node_viewmodels[node.id] = node_vm
            self.graph.add_node(node)
            self._sync_counter_from_id(node.type_name, node.id)

            if node.type_name == "source":
                self._source_node_id = node.id
            elif node.type_name == "preview":
                self._preview_node_id = node.id

            self.nodeAdded.emit(node_vm)
            self.nodeChanged.emit(node.id)

        for connection in document.connections:
            self.graph.connect(
                connection.source_node_id,
                connection.source_port,
                connection.target_node_id,
                connection.target_port,
            )
            self.connectionAdded.emit(connection)

        impacted = set(self.graph.nodes)
        if impacted:
            self.force_reprocess(impacted)
        else:
            self.previewUpdated.emit(None)

    def _clear_graph_state(self) -> None:
        existing_connections = self.graph.list_connections()
        existing_node_ids = list(self.node_viewmodels)

        self._debounce_timer.stop()
        self._latest_requested_generation += 1
        self.graph = Graph()
        self.node_viewmodels = {}
        self._node_counters = defaultdict(int)
        self._results = {}
        self._node_visuals = {}
        self._source_node_id = None
        self._preview_node_id = None
        self._selected_node_id = None
        self._pending_invalidated.clear()

        for connection in existing_connections:
            self.connectionRemoved.emit(connection)
        for node_id in existing_node_ids:
            self.nodeRemoved.emit(node_id)

        self.selectedNodeChanged.emit(None)
        self.previewUpdated.emit(None)

    def _sync_counter_from_id(self, node_type: str, node_id: str) -> None:
        match = re.fullmatch(rf"{re.escape(node_type)}-(\d+)", node_id)
        if match is None:
            return
        self._node_counters[node_type] = max(self._node_counters[node_type], int(match.group(1)))
