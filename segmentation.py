"""Member 2: Otsu, morphology, connected components and optional watershed."""
from dataclasses import dataclass
import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import h_maxima


@dataclass
class GrainRegion:
    grain_id: int
    bbox: tuple
    mask: np.ndarray
    contour: np.ndarray
    centroid: tuple
    touches_border: bool
    was_split: bool = False


@dataclass
class SegmentationResult:
    binary: np.ndarray
    labels: np.ndarray
    regions: list
    threshold: float
    foreground: str
    warnings: list


def _split_component(mask, min_area):
    """Use separated distance maxima as seeds; avoid splitting a thin grain into many pieces."""
    distance = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    smooth = cv2.GaussianBlur(distance, (5, 5), 0)
    height = max(1.0, float(distance.max()) * 0.22)
    maxima = h_maxima(smooth, height) & mask
    count, seeds = cv2.connectedComponents(maxima.astype(np.uint8))
    if count <= 2:
        return [mask]
    centers = []
    for seed_id in range(1, count):
        ys, xs = np.where(seeds == seed_id)
        best = np.argmax(smooth[ys, xs])
        centers.append((float(smooth[ys[best], xs[best]]), int(ys[best]), int(xs[best])))
    chosen = []
    for peak, y, x in sorted(centers, reverse=True):
        if all(np.hypot(y - yy, x - xx) >= max(3, min(peak, pp) * 1.25) for pp, yy, xx in chosen):
            chosen.append((peak, y, x))
    if len(chosen) < 2:
        return [mask]
    markers = np.zeros(mask.shape, np.int32)
    markers[~mask] = 1
    for i, (_, y, x) in enumerate(chosen, 2):
        markers[y, x] = i
    relief = np.uint8(255 - cv2.normalize(smooth, None, 0, 255, cv2.NORM_MINMAX))
    cv2.watershed(cv2.cvtColor(relief, cv2.COLOR_GRAY2BGR), markers)
    valid = (markers > 1) & mask
    if not valid.any():
        return [mask]
    # Assign watershed boundaries/background leakage to the nearest surviving seed region.
    nearest = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    filled = markers[tuple(nearest)]
    parts = [(filled == i) & mask for i in range(2, len(chosen) + 2)]
    if any(int(p.sum()) < min_area for p in parts):
        return [mask]
    return parts


def segment_grains(gray, min_area=12, foreground='auto', opening=1, closing=1, watershed=True, threshold_override=None):
    if gray.ndim != 2 or gray.dtype != np.uint8:
        raise ValueError('Phân đoạn cần ảnh xám uint8.')
    if min_area < 1 or opening < 0 or closing < 0:
        raise ValueError('Diện tích tối thiểu dương, số lần hình thái học không âm.')
    if foreground not in {'auto', 'bright', 'dark'}:
        raise ValueError('foreground phải là auto, bright hoặc dark.')
    threshold, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if threshold_override is not None:
        if not 0 <= threshold_override <= 255:
            raise ValueError('Ngưỡng thủ công phải nằm trong [0,255].')
        threshold, binary = cv2.threshold(gray, float(threshold_override), 255, cv2.THRESH_BINARY)
    if foreground == 'auto':
        border = np.concatenate((binary[0], binary[-1], binary[:, 0], binary[:, -1]))
        foreground = 'dark' if np.mean(border > 0) > 0.5 else 'bright'
    if foreground == 'dark':
        binary = cv2.bitwise_not(binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    if opening:
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=opening)
    if closing:
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=closing)
    # Fill only enclosed holes, retaining the outside boundary.
    binary = ndi.binary_fill_holes(binary > 0).astype(np.uint8) * 255
    n, components, stats, _ = cv2.connectedComponentsWithStats(binary)
    labels = np.zeros(gray.shape, np.int32)
    regions = []
    clean = np.zeros_like(binary)
    for component_id in range(1, n):
        x, y, w, h, area = map(int, stats[component_id])
        if area < min_area:
            continue
        # Padding lets watershed see background even when the bounding box is tight.
        x0, y0 = max(0, x - 2), max(0, y - 2)
        x1, y1 = min(gray.shape[1], x + w + 2), min(gray.shape[0], y + h + 2)
        local = components[y0:y1, x0:x1] == component_id
        contours, _ = cv2.findContours(local.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea)
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        solidity = cv2.contourArea(contour) / hull_area if hull_area else 1.0
        parts = _split_component(local, min_area) if watershed and solidity < 0.97 else [local]
        for part in parts:
            ys, xs = np.where(part)
            px, py = int(xs.min()), int(ys.min())
            pw, ph = int(xs.max() - px + 1), int(ys.max() - py + 1)
            roi = part[py:py+ph, px:px+pw].astype(np.uint8) * 255
            cc, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour = max(cc, key=cv2.contourArea)
            gx, gy = x0 + px, y0 + py
            contour = contour + np.array([[[gx, gy]]], np.int32)
            grain_id = len(regions) + 1
            labels[gy:gy+ph, gx:gx+pw][roi > 0] = grain_id
            clean[gy:gy+ph, gx:gx+pw][roi > 0] = 255
            touches = gx == 0 or gy == 0 or gx+pw == gray.shape[1] or gy+ph == gray.shape[0]
            regions.append(GrainRegion(grain_id, (gx, gy, pw, ph), roi, contour,
                                       (float(xs.mean()+x0), float(ys.mean()+y0)), touches, len(parts) > 1))
    warnings = []
    if not regions:
        warnings.append('Không phát hiện vùng hợp lệ; kiểm tra nền, ánh sáng và diện tích tối thiểu.')
    if np.mean(clean > 0) > 0.6:
        warnings.append('Tiền cảnh chiếm hơn 60% ảnh; kiểm tra lựa chọn nền và các hạt chồng lấp.')
    if any(r.was_split for r in regions):
        warnings.append('Có vùng được tách bằng Watershed; cần kiểm tra bằng mắt trước khi gán nhãn chuẩn.')
    return SegmentationResult(clean, labels, regions, float(threshold), foreground, warnings)
