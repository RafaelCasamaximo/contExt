from __future__ import annotations

from typing import Mapping

import cv2
import numpy as np

from ..pipeline.node import ImageArray, Node, NodeVisuals


DEFAULT_CLAHE_CLIP_LIMIT = 2.0
DEFAULT_CLAHE_TILE_GRID_SIZE = 8
DEFAULT_GABOR_KERNEL_SIZE = 11
DEFAULT_GABOR_SIGMA = 4.0
DEFAULT_GABOR_THETA = 0.0
DEFAULT_GABOR_LAMBDA = 10.0
DEFAULT_GABOR_GAMMA = 0.5
DEFAULT_GABOR_PSI = 0.0
DEFAULT_FREQUENCY_CUTOFF = 24
DEFAULT_FREQUENCY_BAND_MIN = 12
DEFAULT_FREQUENCY_BAND_MAX = 48


def _normalize_odd(value: object, minimum: int = 1, maximum: int = 31) -> int:
    normalized = max(minimum, int(value))
    if normalized % 2 == 0:
        normalized += 1
    return min(normalized, maximum)


def _normalize_int(value: object, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def _normalize_float(value: object, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _normalize_bool(value: object) -> bool:
    return bool(value)


def _rgb_to_gray(image: ImageArray) -> ImageArray:
    if len(image.shape) == 2:
        return image.copy()
    if image.shape[2] == 1:
        return image[:, :, 0].copy()
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def _gray_to_rgb(image: ImageArray) -> ImageArray:
    if len(image.shape) == 3 and image.shape[2] == 3:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)


def _fft_preview_image(spectrum: np.ndarray) -> ImageArray:
    magnitude = np.log1p(np.abs(spectrum))
    normalized = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    return _gray_to_rgb(normalized.astype(np.uint8))


def _ensure_rgb(image: ImageArray | None) -> ImageArray | None:
    if image is None:
        return None
    if len(image.shape) == 2:
        return _gray_to_rgb(image)
    return image.copy()


class CropNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="crop",
            title="Crop",
            input_ports=("image",),
            output_ports=("image",),
            params={"start_x": 0, "start_y": 0, "end_x": 0, "end_y": 0},
        )

    def set_param(self, key: str, value: object) -> None:
        if key in {"start_x", "start_y", "end_x", "end_y"}:
            value = max(0, int(value))
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None

        height, width = image.shape[:2]
        start_x = min(max(0, int(self.params.get("start_x", 0))), width)
        start_y = min(max(0, int(self.params.get("start_y", 0))), height)
        end_x = width if int(self.params.get("end_x", 0)) <= 0 else min(width, int(self.params["end_x"]))
        end_y = height if int(self.params.get("end_y", 0)) <= 0 else min(height, int(self.params["end_y"]))
        if start_x >= end_x or start_y >= end_y:
            return None
        return image[start_y:end_y, start_x:end_x].copy()


class HistogramEqualizationNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="histogram_equalization",
            title="Histogram Equalization",
            input_ports=("image",),
            output_ports=("image",),
            params={},
        )

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        image_yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
        image_yuv[:, :, 0] = cv2.equalizeHist(image_yuv[:, :, 0])
        return cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)


class ClaheEqualizationNode(Node):
    def __init__(
        self,
        node_id: str,
        clip_limit: float = DEFAULT_CLAHE_CLIP_LIMIT,
        tile_grid_size: int = DEFAULT_CLAHE_TILE_GRID_SIZE,
    ) -> None:
        super().__init__(
            id=node_id,
            type_name="clahe_equalization",
            title="CLAHE",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "clip_limit": _normalize_float(clip_limit, 0.1, 20.0),
                "tile_grid_size": _normalize_int(tile_grid_size, 1, 32),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "clip_limit":
            value = _normalize_float(value, 0.1, 20.0)
        elif key == "tile_grid_size":
            value = _normalize_int(value, 1, 32)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        clip_limit = _normalize_float(self.params.get("clip_limit", DEFAULT_CLAHE_CLIP_LIMIT), 0.1, 20.0)
        tile_grid_size = _normalize_int(self.params.get("tile_grid_size", DEFAULT_CLAHE_TILE_GRID_SIZE), 1, 32)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
        image_yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
        image_yuv[:, :, 0] = clahe.apply(image_yuv[:, :, 0])
        return cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)


class BrightnessContrastNode(Node):
    def __init__(self, node_id: str, brightness: int = 0, contrast: float = 1.0) -> None:
        super().__init__(
            id=node_id,
            type_name="brightness_contrast",
            title="Brightness / Contrast",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "brightness": _normalize_int(brightness, -255, 255),
                "contrast": _normalize_float(contrast, 0.1, 5.0),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "brightness":
            value = _normalize_int(value, -255, 255)
        elif key == "contrast":
            value = _normalize_float(value, 0.1, 5.0)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        alpha = _normalize_float(self.params.get("contrast", 1.0), 0.1, 5.0)
        beta = _normalize_int(self.params.get("brightness", 0), -255, 255)
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


class AverageBlurNode(Node):
    def __init__(self, node_id: str, kernel_size: int = 5) -> None:
        super().__init__(
            id=node_id,
            type_name="average_blur",
            title="Average Blur",
            input_ports=("image",),
            output_ports=("image",),
            params={"kernel_size": _normalize_odd(kernel_size)},
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "kernel_size":
            value = _normalize_odd(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        kernel_size = _normalize_odd(self.params.get("kernel_size", 5))
        kernel = np.ones((kernel_size, kernel_size), np.float32) / float(kernel_size * kernel_size)
        return cv2.filter2D(image, -1, kernel)


class GaussianBlurNode(Node):
    def __init__(self, node_id: str, kernel_size: int = 5, type_name: str = "gaussian_blur", title: str = "Gaussian Blur") -> None:
        super().__init__(
            id=node_id,
            type_name=type_name,
            title=title,
            input_ports=("image",),
            output_ports=("image",),
            params={"kernel_size": _normalize_odd(kernel_size)},
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "kernel_size":
            value = _normalize_odd(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        kernel_size = _normalize_odd(self.params.get("kernel_size", 5))
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


class MedianBlurNode(Node):
    def __init__(self, node_id: str, kernel_size: int = 5) -> None:
        super().__init__(
            id=node_id,
            type_name="median_blur",
            title="Median Blur",
            input_ports=("image",),
            output_ports=("image",),
            params={"kernel_size": _normalize_odd(kernel_size)},
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "kernel_size":
            value = _normalize_odd(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        return cv2.medianBlur(image, _normalize_odd(self.params.get("kernel_size", 5)))


class GaborFilterNode(Node):
    def __init__(
        self,
        node_id: str,
        kernel_size: int = DEFAULT_GABOR_KERNEL_SIZE,
        sigma: float = DEFAULT_GABOR_SIGMA,
        theta_deg: float = DEFAULT_GABOR_THETA,
        lambda_value: float = DEFAULT_GABOR_LAMBDA,
        gamma: float = DEFAULT_GABOR_GAMMA,
        psi_deg: float = DEFAULT_GABOR_PSI,
    ) -> None:
        super().__init__(
            id=node_id,
            type_name="gabor_filter",
            title="Gabor Filter",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "kernel_size": _normalize_odd(kernel_size, 1, 51),
                "sigma": _normalize_float(sigma, 0.1, 20.0),
                "theta_deg": float(theta_deg),
                "lambda_value": _normalize_float(lambda_value, 0.1, 100.0),
                "gamma": _normalize_float(gamma, 0.01, 5.0),
                "psi_deg": float(psi_deg),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "kernel_size":
            value = _normalize_odd(value, 1, 51)
        elif key == "sigma":
            value = _normalize_float(value, 0.1, 20.0)
        elif key == "theta_deg":
            value = float(value)
        elif key == "lambda_value":
            value = _normalize_float(value, 0.1, 100.0)
        elif key == "gamma":
            value = _normalize_float(value, 0.01, 5.0)
        elif key == "psi_deg":
            value = float(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        grayscale = _rgb_to_gray(image)
        kernel_size = _normalize_odd(self.params.get("kernel_size", DEFAULT_GABOR_KERNEL_SIZE), 1, 51)
        sigma = _normalize_float(self.params.get("sigma", DEFAULT_GABOR_SIGMA), 0.1, 20.0)
        theta = np.deg2rad(float(self.params.get("theta_deg", DEFAULT_GABOR_THETA)))
        lambd = _normalize_float(self.params.get("lambda_value", DEFAULT_GABOR_LAMBDA), 0.1, 100.0)
        gamma = _normalize_float(self.params.get("gamma", DEFAULT_GABOR_GAMMA), 0.01, 5.0)
        psi = np.deg2rad(float(self.params.get("psi_deg", DEFAULT_GABOR_PSI)))
        kernel = cv2.getGaborKernel((kernel_size, kernel_size), sigma, theta, lambd, gamma, psi, ktype=cv2.CV_32F)
        filtered = cv2.filter2D(grayscale.astype(np.float32), cv2.CV_32F, kernel)
        normalized = cv2.normalize(np.abs(filtered), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return _gray_to_rgb(normalized)


class FrequencyDomainFilterNode(Node):
    VALID_MODES = {"none", "low_pass", "high_pass", "band_pass", "band_stop"}
    PREVIEW_KEY = "frequency_spectrum"

    def __init__(
        self,
        node_id: str,
        mode: str = "none",
        cutoff: int = DEFAULT_FREQUENCY_CUTOFF,
        band_min: int = DEFAULT_FREQUENCY_BAND_MIN,
        band_max: int = DEFAULT_FREQUENCY_BAND_MAX,
    ) -> None:
        super().__init__(
            id=node_id,
            type_name="frequency_domain_filter",
            title="Frequency-domain Filter",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "mode": self._normalize_mode(mode),
                "cutoff": _normalize_int(cutoff, 1, 2048),
                "band_min": _normalize_int(band_min, 1, 2048),
                "band_max": _normalize_int(band_max, 1, 2048),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "mode":
            value = self._normalize_mode(value)
        elif key in {"cutoff", "band_min", "band_max"}:
            value = _normalize_int(value, 1, 2048)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        result, _ = self.process_with_visuals(inputs)
        return result

    def process_with_visuals(
        self,
        inputs: Mapping[str, ImageArray | None],
    ) -> tuple[ImageArray | None, NodeVisuals]:
        image = inputs.get("image")
        if image is None:
            return None, {self.PREVIEW_KEY: None}

        reconstructed, spectrum_preview = self._apply_frequency_filter(image)
        return reconstructed, {self.PREVIEW_KEY: spectrum_preview}

    def _apply_frequency_filter(self, image: ImageArray) -> tuple[ImageArray, ImageArray]:
        grayscale = _rgb_to_gray(image).astype(np.float32)
        shifted = np.fft.fftshift(np.fft.fft2(grayscale))
        masked_shifted = shifted * self._base_mask(grayscale.shape)
        reconstructed = np.fft.ifft2(np.fft.ifftshift(masked_shifted))
        reconstructed = np.clip(np.real(reconstructed), 0, 255).astype(np.uint8)
        spectrum_preview = _fft_preview_image(masked_shifted)
        return _gray_to_rgb(reconstructed), spectrum_preview

    def _base_mask(self, shape: tuple[int, int]) -> np.ndarray:
        mode = self._normalize_mode(self.params.get("mode", "none"))
        cutoff = _normalize_int(self.params.get("cutoff", DEFAULT_FREQUENCY_CUTOFF), 1, 2048)
        band_min = _normalize_int(self.params.get("band_min", DEFAULT_FREQUENCY_BAND_MIN), 1, 2048)
        band_max = _normalize_int(self.params.get("band_max", DEFAULT_FREQUENCY_BAND_MAX), 1, 2048)
        if band_min > band_max:
            band_min, band_max = band_max, band_min

        rows, cols = shape
        center_y = rows // 2
        center_x = cols // 2
        yy, xx = np.ogrid[:rows, :cols]
        distance = np.sqrt((yy - center_y) ** 2 + (xx - center_x) ** 2)

        if mode == "low_pass":
            return (distance <= cutoff).astype(np.float32)
        if mode == "high_pass":
            return (distance >= cutoff).astype(np.float32)
        if mode == "band_pass":
            return ((distance >= band_min) & (distance <= band_max)).astype(np.float32)
        if mode == "band_stop":
            return ((distance < band_min) | (distance > band_max)).astype(np.float32)
        return np.ones((rows, cols), dtype=np.float32)

    @classmethod
    def _normalize_mode(cls, value: object) -> str:
        mode = str(value)
        if mode not in cls.VALID_MODES:
            return "none"
        return mode


class GrayscaleNode(Node):
    def __init__(
        self,
        node_id: str,
        exclude_red: bool = False,
        exclude_green: bool = False,
        exclude_blue: bool = False,
    ) -> None:
        super().__init__(
            id=node_id,
            type_name="grayscale",
            title="Grayscale",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "exclude_red": _normalize_bool(exclude_red),
                "exclude_green": _normalize_bool(exclude_green),
                "exclude_blue": _normalize_bool(exclude_blue),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key in {"exclude_red", "exclude_green", "exclude_blue"}:
            value = _normalize_bool(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        adjusted = image.copy()
        if _normalize_bool(self.params.get("exclude_blue", False)):
            adjusted[:, :, 2] = 0
        if _normalize_bool(self.params.get("exclude_green", False)):
            adjusted[:, :, 1] = 0
        if _normalize_bool(self.params.get("exclude_red", False)):
            adjusted[:, :, 0] = 0
        gray = cv2.cvtColor(adjusted, cv2.COLOR_RGB2GRAY)
        return _gray_to_rgb(gray)


class LaplacianNode(Node):
    def __init__(self, node_id: str, kernel_size: int = 1) -> None:
        super().__init__(
            id=node_id,
            type_name="laplacian",
            title="Laplacian",
            input_ports=("image",),
            output_ports=("image",),
            params={"kernel_size": _normalize_odd(kernel_size, 1, 15)},
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "kernel_size":
            value = _normalize_odd(value, 1, 15)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        kernel_size = _normalize_odd(self.params.get("kernel_size", 1), 1, 15)
        return cv2.Laplacian(image, cv2.CV_8U, ksize=kernel_size)


class SobelNode(Node):
    VALID_AXES = {"x_axis", "y_axis", "xy_axis"}

    def __init__(self, node_id: str, axis: str = "x_axis") -> None:
        super().__init__(
            id=node_id,
            type_name="sobel",
            title="Sobel",
            input_ports=("image",),
            output_ports=("image",),
            params={"axis": self._normalize_axis(axis)},
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "axis":
            value = self._normalize_axis(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = _ensure_rgb(inputs.get("image"))
        if image is None:
            return None
        axis = self._normalize_axis(self.params.get("axis", "x_axis"))
        if axis == "x_axis":
            return cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3)
        if axis == "y_axis":
            return cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3)
        sobel_x = cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=3)
        return cv2.bitwise_or(sobel_x, sobel_y)

    @classmethod
    def _normalize_axis(cls, value: object) -> str:
        axis = str(value)
        if axis not in cls.VALID_AXES:
            return "x_axis"
        return axis


class GlobalThresholdNode(Node):
    def __init__(self, node_id: str, threshold: int = 127, invert: bool = False) -> None:
        super().__init__(
            id=node_id,
            type_name="global_threshold",
            title="Global Threshold",
            input_ports=("image",),
            output_ports=("image",),
            params={
                "threshold": _normalize_int(threshold, 0, 255),
                "invert": _normalize_bool(invert),
            },
        )

    def set_param(self, key: str, value: object) -> None:
        if key == "threshold":
            value = _normalize_int(value, 0, 255)
        elif key == "invert":
            value = _normalize_bool(value)
        super().set_param(key, value)

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        threshold = _normalize_int(self.params.get("threshold", 127), 0, 255)
        threshold_mode = cv2.THRESH_BINARY_INV if _normalize_bool(self.params.get("invert", False)) else cv2.THRESH_BINARY
        _, thresholded = cv2.threshold(image, threshold, 255, threshold_mode)
        return _gray_to_rgb(thresholded) if len(thresholded.shape) == 2 else thresholded


class AdaptiveMeanThresholdNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="adaptive_mean_threshold",
            title="Adaptive Mean Threshold",
            input_ports=("image",),
            output_ports=("image",),
            params={},
        )

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        gray = _rgb_to_gray(image)
        thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
        return _gray_to_rgb(thresholded)


class AdaptiveGaussianThresholdNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="adaptive_gaussian_threshold",
            title="Adaptive Gaussian Threshold",
            input_ports=("image",),
            output_ports=("image",),
            params={},
        )

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        gray = _rgb_to_gray(image)
        thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return _gray_to_rgb(thresholded)


class OtsuBinarizationNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(
            id=node_id,
            type_name="otsu_binarization",
            title="Otsu Binarization",
            input_ports=("image",),
            output_ports=("image",),
            params={},
        )

    def process(self, inputs: Mapping[str, ImageArray | None]) -> ImageArray | None:
        image = inputs.get("image")
        if image is None:
            return None
        gray = _rgb_to_gray(image)
        _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return _gray_to_rgb(thresholded)
