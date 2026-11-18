"""Member 3: shape, masked RGB/HSV and masked gray-level co-occurrence."""
import cv2
import numpy as np
import pandas as pd
from skimage.feature import graycoprops

COLOR_DEFAULTS = dict(yellow_h_min=10, yellow_h_max=40, yellow_s_min=55,
                      yellow_v_min=65, dark_v_max=85)
FEATURE_COLUMNS = ['grain_id', 'area', 'pixel_area', 'perimeter', 'length', 'width',
                   'aspect_ratio', 'circularity', 'solidity', 'mean_r', 'mean_g', 'mean_b',
                   'mean_h', 'mean_s', 'mean_v', 'yellow_fraction', 'dark_fraction', 'color_pixel_count',
                   'glcm_contrast', 'glcm_homogeneity', 'glcm_energy', 'glcm_correlation',
                   'texture_pairs', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h',
                   'center_x', 'center_y', 'touches_border', 'was_split', 'feature_valid',
                   'object_type', 'exclusion_reason']


def masked_glcm(gray, mask, levels=32):
    """Count only pairs whose BOTH endpoints are in the grain (no background texture)."""
    q = np.minimum(gray.astype(np.int32) * levels // 256, levels - 1)
    matrices = []
    pair_count = 0
    h, w = gray.shape
    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        ya, yb = slice(max(0, -dy), min(h, h-dy)), slice(max(0, dy), min(h, h+dy))
        xa, xb = slice(max(0, -dx), min(w, w-dx)), slice(max(0, dx), min(w, w+dx))
        valid = mask[ya, xa] & mask[yb, xb]
        a, b = q[ya, xa][valid], q[yb, xb][valid]
        if not a.size:
            continue
        matrix = np.bincount(a * levels + b, minlength=levels*levels).reshape(levels, levels).astype(float)
        matrix += matrix.T
        matrices.append(matrix / matrix.sum())
        pair_count += int(a.size)
    if not matrices:
        return {**{f'glcm_{k}': np.nan for k in ['contrast', 'homogeneity', 'energy', 'correlation']}, 'texture_pairs': 0}
    glcm = np.stack(matrices, axis=-1)[:, :, None, :]
    return {**{f'glcm_{k}': float(graycoprops(glcm, k).mean()) for k in ['contrast', 'homogeneity', 'energy', 'correlation']},
            'texture_pairs': pair_count}


def extract_features(preprocessed, segmentation, color_rules=None, texture=True, exclude_large_round=True):
    rules = {**COLOR_DEFAULTS, **(color_rules or {})}
    if not 0 <= rules['yellow_h_min'] <= rules['yellow_h_max'] <= 179:
        raise ValueError('Khoảng H phải thỏa 0 <= H_min <= H_max <= 179 theo OpenCV.')
    if any(not 0 <= rules[k] <= 255 for k in ['yellow_s_min','yellow_v_min','dark_v_max']):
        raise ValueError('Ngưỡng S và V phải nằm trong [0,255].')
    rows = []
    sx, sy = preprocessed.scale_x, preprocessed.scale_y
    for region in segmentation.regions:
        x, y, w, h = region.bbox
        mask = region.mask > 0
        color = preprocessed.color[y:y+h, x:x+w]
        hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)
        # Otsu/blur can add a thin background halo; sample the interior for color.
        core = cv2.erode(region.mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)),
                         borderType=cv2.BORDER_CONSTANT,borderValue=0) > 0
        color_mask = core if core.sum() >= max(3, mask.sum()*0.5) else mask
        pixels, hp = color[color_mask], hsv[color_mask]
        contour = region.contour.astype(np.float32) / np.array([sx, sy], np.float32)
        area = float(cv2.contourArea(contour))
        perimeter = float(cv2.arcLength(contour, True))
        length, width = sorted(cv2.minAreaRect(contour)[1], reverse=True)
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        yellow = ((hp[:, 0] >= rules['yellow_h_min']) & (hp[:, 0] <= rules['yellow_h_max']) &
                  (hp[:, 1] >= rules['yellow_s_min']) & (hp[:, 2] >= rules['yellow_v_min']))
        b, g, r = pixels.mean(axis=0)
        mh, ms, mv = hp.mean(axis=0)
        row = dict(grain_id=region.grain_id, area=area, pixel_area=float(mask.sum()/(sx*sy)),
                   perimeter=perimeter, length=float(length), width=float(width),
                   aspect_ratio=float(length/width) if width else 0.0,
                   circularity=float(4*np.pi*area/perimeter**2) if perimeter else 0.0,
                   solidity=float(area/hull_area) if hull_area else 0.0,
                   mean_r=float(r), mean_g=float(g), mean_b=float(b), mean_h=float(mh), mean_s=float(ms), mean_v=float(mv),
                   yellow_fraction=float(yellow.mean()), dark_fraction=float((hp[:, 2] <= rules['dark_v_max']).mean()),
                   color_pixel_count=int(color_mask.sum()),
                   bbox_x=x/sx, bbox_y=y/sy, bbox_w=w/sx, bbox_h=h/sy,
                   center_x=region.centroid[0]/sx, center_y=region.centroid[1]/sy,
                   touches_border=region.touches_border, was_split=region.was_split,
                   feature_valid=bool(area > 0 and width > 0), object_type='candidate_grain', exclusion_reason='')
        row.update(masked_glcm(preprocessed.gray[y:y+h, x:x+w], mask) if texture else
                   {**{f'glcm_{k}': np.nan for k in ['contrast', 'homogeneity', 'energy', 'correlation']}, 'texture_pairs': 0})
        rows.append(row)
    frame = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    # A conservative, optional coin/large-object filter, not a general impurity detector.
    if len(frame) and exclude_large_round:
        median = float(frame.pixel_area.median())
        excluded = (frame.pixel_area > median*5) & (frame.aspect_ratio < 1.4) & (frame.circularity > 0.70)
        frame.loc[excluded, 'object_type'] = 'excluded_object'
        frame.loc[excluded, 'exclusion_reason'] = 'large_round_object'
    return frame
