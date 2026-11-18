"""Reusable integration layer, shared by the CLI and Streamlit UI."""
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
import json
import cv2
import numpy as np
from preprocessing import preprocess_image
from segmentation import segment_grains
from feature_extraction import extract_features, COLOR_DEFAULTS
from classification import classify_grains, validate_rules
from rice_statistics import summarize_results, create_statistics_figure
from image_io import read_image, write_image


@dataclass
class PipelineConfig:
    max_side: int = 1600
    blur_kernel: int = 3
    contrast: str = 'none'
    foreground: str = 'auto'
    min_area: int = 12
    threshold_override: float | None = None
    opening: int = 1
    closing: int = 1
    watershed: bool = True
    texture: bool = True
    exclude_large_round: bool = True
    rules: dict = field(default_factory=dict)
    color_rules: dict = field(default_factory=lambda: COLOR_DEFAULTS.copy())


@dataclass
class AnalysisResult:
    preprocessing: object
    segmentation: object
    features: object
    classified: object
    summary: dict
    distribution: object
    annotated: np.ndarray
    warnings: list
    config: PipelineConfig


def analyze_image(image, config=None):
    config = config or PipelineConfig()
    rules = validate_rules(config.rules)
    config = replace(config, rules=rules, color_rules={**COLOR_DEFAULTS, **config.color_rules})
    pre = preprocess_image(image, config.max_side, config.blur_kernel, config.contrast)
    seg = segment_grains(pre.enhanced, config.min_area, config.foreground, config.opening, config.closing, config.watershed, config.threshold_override)
    features = extract_features(pre, seg, config.color_rules, config.texture, config.exclude_large_round)
    classified = classify_grains(features, rules)
    summary, distribution = summarize_results(classified)
    warnings = list(seg.warnings)
    if config.threshold_override is not None:
        warnings.append('Đang sử dụng ngưỡng phân đoạn thủ công thay cho Otsu.')
    if not rules['calibrated']:
        warnings.append('Bộ ngưỡng thử nghiệm chưa được xác nhận trên dữ liệu gán nhãn độc lập.')
    if rules['reference_length_px'] is None:
        warnings.append('Chưa đặt chiều dài chuẩn: nhãn hình dạng để Không xác định.')
    if summary['excluded_objects']:
        warnings.append(f"Đã loại {summary['excluded_objects']} vùng lớn gần tròn; kiểm tra đó có phải đồng xu/vật lạ.")
    annotated = pre.color.copy()
    for region, row in zip(seg.regions, classified.itertuples()):
        if row.object_type == 'excluded_object':
            color, label = (160, 160, 160), f'{row.grain_id}: X'
        else:
            color = (70, 190, 90) if row.conclusion == 'Đạt tiêu chí ảnh đã chọn' else (30, 170, 240)
            if row.conclusion == 'Có dấu hiệu lỗi':
                color = (70, 70, 230)
            shape = {'Nguyên':'N', 'Vỡ':'V', 'Không xác định':'?'}[row.shape_label]
            hue = {'Bình thường':'BT', 'Vàng':'Y', 'Sẫm':'S', 'Không xác định':'?'}[row.color_label]
            label = f'{row.grain_id}:{shape}/{hue}'
        cv2.drawContours(annotated, [region.contour], -1, color, 1, cv2.LINE_AA)
        x, y, _, _ = region.bbox
        cv2.putText(annotated, label, (x, max(10, y-3)), cv2.FONT_HERSHEY_SIMPLEX, .32, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(annotated, label, (x, max(10, y-3)), cv2.FONT_HERSHEY_SIMPLEX, .32, color, 1, cv2.LINE_AA)
    return AnalysisResult(pre, seg, features, classified, summary, distribution, annotated, warnings, config)


def analyze_file(path, config=None):
    return analyze_image(read_image(path), config)


def export_result(result, output_dir, source_path=None, export_rois=True):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in [('color', result.preprocessing.color), ('gray', result.preprocessing.gray),
                       ('denoised', result.preprocessing.denoised), ('enhanced', result.preprocessing.enhanced),
                       ('mask', result.segmentation.binary), ('annotated', result.annotated)]:
        write_image(output / f'{name}.png', data)
    np.save(output / 'instance_labels.npy', result.segmentation.labels, allow_pickle=False)
    for name, frame in [('features',result.features), ('classification',result.classified), ('statistics',result.distribution)]:
        frame.to_csv(output / f'{name}.csv', index=False, encoding='utf-8-sig')
    details = dict(summary=result.summary, warnings=result.warnings, config=asdict(result.config),
                   source_path=str(source_path) if source_path else None,
                   original_shape=result.preprocessing.original_shape,
                   scale_x=result.preprocessing.scale_x, scale_y=result.preprocessing.scale_y,
                   segmentation_threshold=result.segmentation.threshold,
                   threshold_method='manual' if result.config.threshold_override is not None else 'otsu',
                   foreground=result.segmentation.foreground,
                   units='length/width/perimeter: original-image px; area: original-image px^2; fractions: 0..1')
    (output / 'summary.json').write_text(json.dumps(details, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    fig = create_statistics_figure(result.distribution)
    fig.savefig(output / 'statistics.png', dpi=150)
    import matplotlib.pyplot as plt
    plt.close(fig)
    if export_rois:
        for region in result.segmentation.regions:
            x, y, w, h = region.bbox
            write_image(output / 'rois' / f'grain_{region.grain_id:04d}_color.png', result.preprocessing.color[y:y+h,x:x+w])
            write_image(output / 'rois' / f'grain_{region.grain_id:04d}_mask.png', region.mask)
    # Empty manual labels: algorithm predictions are kept in classification.csv, never called ground truth.
    labels = result.features[['grain_id','bbox_x','bbox_y','bbox_w','bbox_h']].copy()
    labels.insert(0, 'image_path', str(source_path) if source_path else '')
    for col in ['shape_label','color_label','reviewer','notes']:
        labels[col] = ''
    labels['verified'] = False
    target = output / 'grain_labels_template.csv'
    if not target.exists():  # Never overwrite manual annotation work on rerun.
        labels.to_csv(target, index=False, encoding='utf-8-sig')
    return output
