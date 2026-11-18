"""Member 4: independent, explainable if/else rules; no machine learning."""
import math
import pandas as pd

DEFAULT_RULES = dict(reference_length_px=None, whole_min=0.80, broken_max=0.70,
                     yellow_min_fraction=0.25, dark_min_fraction=0.30,
                     normal_max_fraction=0.10, calibrated=False)


def validate_rules(rules):
    r = {**DEFAULT_RULES, **rules}
    if not 0 < r['broken_max'] < r['whole_min'] <= 1.5:
        raise ValueError('Cần 0 < broken_max < whole_min <= 1.5.')
    ref = r['reference_length_px']
    if ref is not None and (not math.isfinite(float(ref)) or float(ref) <= 0):
        raise ValueError('Chiều dài chuẩn phải là số dương, cùng tỷ lệ chụp với ảnh đang xét.')
    if not (0 <= r['normal_max_fraction'] < min(r['yellow_min_fraction'], r['dark_min_fraction']) <= 1):
        raise ValueError('Ngưỡng bình thường phải nhỏ hơn ngưỡng vàng/sẫm; các tỷ lệ nằm trong [0,1].')
    if max(r['yellow_min_fraction'], r['dark_min_fraction']) > 1:
        raise ValueError('Các tỷ lệ màu phải nằm trong [0,1].')
    return r


def classify_shape(features, rules):
    ref = rules.get('reference_length_px')
    if features.get('touches_border') or not features.get('feature_valid', True):
        return 'Không xác định', 'Hạt cắt biên hoặc đặc trưng hình học không hợp lệ.'
    if ref is None:
        return 'Không xác định', 'Chưa có chiều dài hạt nguyên tham chiếu cùng tỷ lệ chụp.'
    ratio = float(features['length']) / ref
    if ratio >= rules['whole_min']:
        return 'Nguyên', 'length/reference >= whole_min'
    elif ratio < rules['broken_max']:
        return 'Vỡ', 'length/reference < broken_max'
    return 'Không xác định', 'Tỷ lệ chiều dài nằm trong vùng chuyển tiếp.'


def classify_color(features, rules):
    if not features.get('feature_valid', True):
        return 'Không xác định', 'Đặc trưng không hợp lệ.'
    yellow, dark = features['yellow_fraction'], features['dark_fraction']
    if not all(math.isfinite(float(v)) for v in (yellow, dark)):
        return 'Không xác định', 'Thiếu đặc trưng màu.'
    if yellow >= rules['yellow_min_fraction'] and dark >= rules['dark_min_fraction']:
        return 'Không xác định', 'Đồng thời nhiều pixel vàng và sẫm; cần kiểm tra.'
    elif dark >= rules['dark_min_fraction']:
        return 'Sẫm', 'Tỷ lệ pixel sẫm đạt ngưỡng.'
    elif yellow >= rules['yellow_min_fraction']:
        return 'Vàng', 'Tỷ lệ pixel vàng đạt ngưỡng.'
    elif max(yellow, dark) <= rules['normal_max_fraction']:
        return 'Bình thường', 'Tỷ lệ pixel vàng và sẫm đều thấp.'
    return 'Không xác định', 'Tỷ lệ màu nằm trong vùng chuyển tiếp.'


def classify_grains(features, rules=None):
    rules = validate_rules(rules or {})
    result = features.copy()
    additions = []
    for _, row in result.iterrows():
        f = row.to_dict()
        if f['object_type'] == 'excluded_object':
            shape, sr, color, cr = 'Không áp dụng', f['exclusion_reason'], 'Không áp dụng', f['exclusion_reason']
            conclusion = 'Vùng bị loại'
        else:
            shape, sr = classify_shape(f, rules)
            color, cr = classify_color(f, rules)
            if shape == 'Vỡ' or color in {'Vàng', 'Sẫm'}:
                conclusion = 'Có dấu hiệu lỗi'
            elif shape == 'Nguyên' and color == 'Bình thường':
                conclusion = 'Đạt tiêu chí ảnh đã chọn'
            else:
                conclusion = 'Cần kiểm tra'
        additions.append(dict(length_ratio=f['length']/rules['reference_length_px'] if rules['reference_length_px'] else None,
                              shape_label=shape, color_label=color, shape_reason=sr, color_reason=cr,
                              conclusion=conclusion, rules_calibrated=rules['calibrated']))
    return pd.concat([result.reset_index(drop=True), pd.DataFrame(additions, columns=[
        'length_ratio', 'shape_label', 'color_label', 'shape_reason', 'color_reason', 'conclusion', 'rules_calibrated'])], axis=1)
