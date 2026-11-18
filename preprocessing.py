"""Member 1: preserve geometry and keep the color measurement branch intact."""
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class PreprocessingResult:
    color: np.ndarray
    gray: np.ndarray
    denoised: np.ndarray
    enhanced: np.ndarray
    scale_x: float
    scale_y: float
    original_shape: tuple


def preprocess_image(image, max_side=1600, blur_kernel=3, contrast='none'):
    if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError('Ảnh phải là mảng BGR uint8 có 3 kênh.')
    if max_side < 32 or blur_kernel < 1 or blur_kernel % 2 == 0:
        raise ValueError('max_side >= 32; nhân Gaussian phải là số lẻ dương.')
    if contrast not in {'none', 'equalize', 'clahe'}:
        raise ValueError('contrast phải là none, equalize hoặc clahe.')
    h, w = image.shape[:2]
    scale = min(1.0, float(max_side) / max(h, w))
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    color = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA) if scale < 1 else image.copy()
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    enhanced = denoised.copy()
    if contrast == 'equalize':
        enhanced = cv2.equalizeHist(denoised)
    elif contrast == 'clahe':
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    return PreprocessingResult(color, gray, denoised, enhanced, nw / w, nh / h, (h, w))
