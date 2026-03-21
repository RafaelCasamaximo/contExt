from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..pipeline.node import Node
from .blur_node import BlurNode
from .filter_nodes import (
    AdaptiveGaussianThresholdNode,
    AdaptiveMeanThresholdNode,
    AverageBlurNode,
    BrightnessContrastNode,
    ClaheEqualizationNode,
    CropNode,
    FrequencyDomainFilterNode,
    GaborFilterNode,
    GaussianBlurNode,
    GlobalThresholdNode,
    GrayscaleNode,
    HistogramEqualizationNode,
    LaplacianNode,
    MedianBlurNode,
    OtsuBinarizationNode,
    SobelNode,
)
from .preview_node import PreviewNode
from .source_node import SourceNode


@dataclass(frozen=True, slots=True)
class NodeOptionDefinition:
    value: object
    label_key: str


@dataclass(frozen=True, slots=True)
class NodeParamDefinition:
    key: str
    label_key: str
    kind: str
    default: object
    minimum: int | float | None = None
    maximum: int | float | None = None
    step: int | float | None = None
    decimals: int = 0
    options: tuple[NodeOptionDefinition, ...] = ()
    inline_slider: bool = False
    odd_only: bool = False


@dataclass(frozen=True, slots=True)
class NodeDefinition:
    type_name: str
    category: str
    title_key: str
    body_key: str
    description_key: str
    factory: Callable[[str], Node]
    singleton: bool = False
    menu_visible: bool = True
    params: tuple[NodeParamDefinition, ...] = field(default_factory=tuple)

    def inline_slider_param(self) -> NodeParamDefinition | None:
        for param in self.params:
            if param.inline_slider and param.kind == "int":
                return param
        return None


MENU_CATEGORY_ORDER = ("input", "processing", "filtering", "frequency", "thresholding", "output")


NODE_DEFINITIONS: dict[str, NodeDefinition] = {
    "source": NodeDefinition(
        type_name="source",
        category="input",
        title_key="node.source.title",
        body_key="node.source.body.empty",
        description_key="panel.source.description",
        factory=SourceNode,
        singleton=True,
    ),
    "crop": NodeDefinition(
        type_name="crop",
        category="processing",
        title_key="node.crop.title",
        body_key="node.crop.body",
        description_key="panel.crop.description",
        factory=CropNode,
        params=(
            NodeParamDefinition("start_x", "param.crop.start_x", "int", 0, 0, 99999, 1),
            NodeParamDefinition("start_y", "param.crop.start_y", "int", 0, 0, 99999, 1),
            NodeParamDefinition("end_x", "param.crop.end_x", "int", 0, 0, 99999, 1),
            NodeParamDefinition("end_y", "param.crop.end_y", "int", 0, 0, 99999, 1),
        ),
    ),
    "histogram_equalization": NodeDefinition(
        type_name="histogram_equalization",
        category="filtering",
        title_key="node.histogram_equalization.title",
        body_key="node.histogram_equalization.body",
        description_key="panel.histogram_equalization.description",
        factory=HistogramEqualizationNode,
    ),
    "clahe_equalization": NodeDefinition(
        type_name="clahe_equalization",
        category="filtering",
        title_key="node.clahe_equalization.title",
        body_key="node.clahe_equalization.body",
        description_key="panel.clahe_equalization.description",
        factory=ClaheEqualizationNode,
        params=(
            NodeParamDefinition("clip_limit", "param.clahe.clip_limit", "float", 2.0, 0.1, 20.0, 0.1, decimals=1),
            NodeParamDefinition("tile_grid_size", "param.clahe.tile_grid_size", "int", 8, 1, 32, 1),
        ),
    ),
    "brightness_contrast": NodeDefinition(
        type_name="brightness_contrast",
        category="filtering",
        title_key="node.brightness_contrast.title",
        body_key="node.brightness_contrast.body",
        description_key="panel.brightness_contrast.description",
        factory=BrightnessContrastNode,
        params=(
            NodeParamDefinition("brightness", "param.brightness_contrast.brightness", "int", 0, -255, 255, 1),
            NodeParamDefinition("contrast", "param.brightness_contrast.contrast", "float", 1.0, 0.1, 5.0, 0.1, decimals=1),
        ),
    ),
    "average_blur": NodeDefinition(
        type_name="average_blur",
        category="filtering",
        title_key="node.average_blur.title",
        body_key="node.average_blur.body",
        description_key="panel.average_blur.description",
        factory=AverageBlurNode,
        params=(
            NodeParamDefinition("kernel_size", "param.kernel_size", "int", 5, 1, 31, 1, inline_slider=True, odd_only=True),
        ),
    ),
    "gaussian_blur": NodeDefinition(
        type_name="gaussian_blur",
        category="filtering",
        title_key="node.gaussian_blur.title",
        body_key="node.gaussian_blur.body",
        description_key="panel.gaussian_blur.description",
        factory=GaussianBlurNode,
        params=(
            NodeParamDefinition("kernel_size", "param.kernel_size", "int", 5, 1, 31, 1, inline_slider=True, odd_only=True),
        ),
    ),
    "blur": NodeDefinition(
        type_name="blur",
        category="filtering",
        title_key="node.blur.title",
        body_key="node.blur.body",
        description_key="panel.blur.description",
        factory=BlurNode,
        menu_visible=False,
        params=(
            NodeParamDefinition("kernel_size", "param.kernel_size", "int", 5, 1, 31, 1, inline_slider=True, odd_only=True),
        ),
    ),
    "median_blur": NodeDefinition(
        type_name="median_blur",
        category="filtering",
        title_key="node.median_blur.title",
        body_key="node.median_blur.body",
        description_key="panel.median_blur.description",
        factory=MedianBlurNode,
        params=(
            NodeParamDefinition("kernel_size", "param.kernel_size", "int", 5, 1, 31, 1, inline_slider=True, odd_only=True),
        ),
    ),
    "gabor_filter": NodeDefinition(
        type_name="gabor_filter",
        category="frequency",
        title_key="node.gabor_filter.title",
        body_key="node.gabor_filter.body",
        description_key="panel.gabor_filter.description",
        factory=GaborFilterNode,
        params=(
            NodeParamDefinition("kernel_size", "param.gabor.kernel_size", "int", 11, 1, 51, 1, odd_only=True),
            NodeParamDefinition("sigma", "param.gabor.sigma", "float", 4.0, 0.1, 20.0, 0.1, decimals=1),
            NodeParamDefinition("theta_deg", "param.gabor.theta_deg", "float", 0.0, -180.0, 180.0, 1.0, decimals=1),
            NodeParamDefinition("lambda_value", "param.gabor.lambda_value", "float", 10.0, 0.1, 100.0, 0.1, decimals=1),
            NodeParamDefinition("gamma", "param.gabor.gamma", "float", 0.5, 0.01, 5.0, 0.01, decimals=2),
            NodeParamDefinition("psi_deg", "param.gabor.psi_deg", "float", 0.0, -180.0, 180.0, 1.0, decimals=1),
        ),
    ),
    "frequency_domain_filter": NodeDefinition(
        type_name="frequency_domain_filter",
        category="frequency",
        title_key="node.frequency_domain_filter.title",
        body_key="node.frequency_domain_filter.body",
        description_key="panel.frequency_domain_filter.description",
        factory=FrequencyDomainFilterNode,
        params=(
            NodeParamDefinition(
                "mode",
                "param.frequency.mode",
                "enum",
                "none",
                options=(
                    NodeOptionDefinition("none", "param.frequency.mode.none"),
                    NodeOptionDefinition("low_pass", "param.frequency.mode.low_pass"),
                    NodeOptionDefinition("high_pass", "param.frequency.mode.high_pass"),
                    NodeOptionDefinition("band_pass", "param.frequency.mode.band_pass"),
                    NodeOptionDefinition("band_stop", "param.frequency.mode.band_stop"),
                ),
            ),
            NodeParamDefinition("cutoff", "param.frequency.cutoff", "int", 24, 1, 2048, 1),
            NodeParamDefinition("band_min", "param.frequency.band_min", "int", 12, 1, 2048, 1),
            NodeParamDefinition("band_max", "param.frequency.band_max", "int", 48, 1, 2048, 1),
        ),
    ),
    "grayscale": NodeDefinition(
        type_name="grayscale",
        category="thresholding",
        title_key="node.grayscale.title",
        body_key="node.grayscale.body",
        description_key="panel.grayscale.description",
        factory=GrayscaleNode,
        params=(
            NodeParamDefinition("exclude_red", "param.grayscale.exclude_red", "bool", False),
            NodeParamDefinition("exclude_green", "param.grayscale.exclude_green", "bool", False),
            NodeParamDefinition("exclude_blue", "param.grayscale.exclude_blue", "bool", False),
        ),
    ),
    "laplacian": NodeDefinition(
        type_name="laplacian",
        category="thresholding",
        title_key="node.laplacian.title",
        body_key="node.laplacian.body",
        description_key="panel.laplacian.description",
        factory=LaplacianNode,
        params=(
            NodeParamDefinition("kernel_size", "param.kernel_size", "int", 1, 1, 15, 1, inline_slider=True, odd_only=True),
        ),
    ),
    "sobel": NodeDefinition(
        type_name="sobel",
        category="thresholding",
        title_key="node.sobel.title",
        body_key="node.sobel.body",
        description_key="panel.sobel.description",
        factory=SobelNode,
        params=(
            NodeParamDefinition(
                "axis",
                "param.sobel.axis",
                "enum",
                "x_axis",
                options=(
                    NodeOptionDefinition("x_axis", "param.sobel.axis.x_axis"),
                    NodeOptionDefinition("y_axis", "param.sobel.axis.y_axis"),
                    NodeOptionDefinition("xy_axis", "param.sobel.axis.xy_axis"),
                ),
            ),
        ),
    ),
    "global_threshold": NodeDefinition(
        type_name="global_threshold",
        category="thresholding",
        title_key="node.global_threshold.title",
        body_key="node.global_threshold.body",
        description_key="panel.global_threshold.description",
        factory=GlobalThresholdNode,
        params=(
            NodeParamDefinition("threshold", "param.global_threshold.threshold", "int", 127, 0, 255, 1, inline_slider=True),
            NodeParamDefinition("invert", "param.global_threshold.invert", "bool", False),
        ),
    ),
    "adaptive_mean_threshold": NodeDefinition(
        type_name="adaptive_mean_threshold",
        category="thresholding",
        title_key="node.adaptive_mean_threshold.title",
        body_key="node.adaptive_mean_threshold.body",
        description_key="panel.adaptive_mean_threshold.description",
        factory=AdaptiveMeanThresholdNode,
    ),
    "adaptive_gaussian_threshold": NodeDefinition(
        type_name="adaptive_gaussian_threshold",
        category="thresholding",
        title_key="node.adaptive_gaussian_threshold.title",
        body_key="node.adaptive_gaussian_threshold.body",
        description_key="panel.adaptive_gaussian_threshold.description",
        factory=AdaptiveGaussianThresholdNode,
    ),
    "otsu_binarization": NodeDefinition(
        type_name="otsu_binarization",
        category="thresholding",
        title_key="node.otsu_binarization.title",
        body_key="node.otsu_binarization.body",
        description_key="panel.otsu_binarization.description",
        factory=OtsuBinarizationNode,
    ),
    "preview": NodeDefinition(
        type_name="preview",
        category="output",
        title_key="node.preview.title",
        body_key="node.preview.body",
        description_key="panel.preview.description",
        factory=PreviewNode,
        singleton=True,
    ),
}


def create_node(node_type: str, node_id: str, params: dict[str, Any] | None = None) -> Node:
    definition = get_node_definition(node_type)
    node = definition.factory(node_id)
    for key, value in (params or {}).items():
        node.set_param(key, value)
    return node


def get_node_definition(node_type: str) -> NodeDefinition:
    try:
        return NODE_DEFINITIONS[node_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported node type '{node_type}'.") from exc


def available_node_definitions(*, menu_only: bool = False) -> tuple[NodeDefinition, ...]:
    definitions = tuple(NODE_DEFINITIONS.values())
    if not menu_only:
        return definitions
    return tuple(definition for definition in definitions if definition.menu_visible)


def grouped_menu_definitions() -> dict[str, tuple[NodeDefinition, ...]]:
    grouped: dict[str, list[NodeDefinition]] = {category: [] for category in MENU_CATEGORY_ORDER}
    for definition in available_node_definitions(menu_only=True):
        grouped.setdefault(definition.category, []).append(definition)
    return {category: tuple(grouped[category]) for category in MENU_CATEGORY_ORDER if grouped.get(category)}


def supported_node_types() -> tuple[str, ...]:
    return tuple(NODE_DEFINITIONS)
