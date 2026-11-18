"""Member 4 statistics. Named rice_statistics to avoid shadowing Python's statistics module."""
import pandas as pd


def summarize_results(frame):
    grains = frame[frame.object_type == 'candidate_grain']
    n = len(grains)
    rows = []
    for axis, column, labels in [('Hình dạng', 'shape_label', ['Nguyên', 'Vỡ', 'Không xác định']),
                                  ('Màu sắc', 'color_label', ['Bình thường', 'Vàng', 'Sẫm', 'Không xác định'])]:
        for label in labels:
            count = int((grains[column] == label).sum())
            rows.append(dict(group=axis, label=label, count=count, percentage=100*count/n if n else 0.0))
    unknown = int(((grains.shape_label == 'Không xác định') | (grains.color_label == 'Không xác định')).sum())
    def mean(col):
        value = grains[col].mean()
        return None if pd.isna(value) else float(value)
    summary = dict(detected_regions=len(frame), total_grains=n, excluded_objects=len(frame)-n,
                   unknown_grains=unknown, mean_area_px2=mean('area'), mean_length_px=mean('length'),
                   mean_h=mean('mean_h'), mean_s=mean('mean_s'), mean_v=mean('mean_v'),
                   border_grains=int(grains.touches_border.sum()),
                   scope='Đánh giá hình dạng và màu sắc quan sát được; ngưỡng cần hiệu chỉnh bằng nhãn chuẩn.')
    return summary, pd.DataFrame(rows)


def create_statistics_figure(distribution):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, group in zip(axes, ['Hình dạng', 'Màu sắc']):
        subset = distribution[distribution.group == group]
        bars = ax.bar(subset.label, subset['count'], color=['#3b8069', '#d6a348', '#7b89a1', '#815b72'][:len(subset)])
        ax.set_title(group)
        ax.set_ylabel('Số hạt')
        ax.tick_params(axis='x', labelsize=9)
        ax.bar_label(bars, labels=[f'{r.count}\n({r.percentage:.1f}%)' for r in subset.itertuples()], padding=3)
        ax.set_ylim(0, max(1, subset['count'].max())*1.3)
    return fig
