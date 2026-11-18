"""Audit source data without inventing per-grain labels or modifying original images."""
from pathlib import Path
import hashlib
import json
import pandas as pd
from image_io import SUPPORTED_EXTENSIONS, read_image, write_image
from preprocessing import preprocess_image


def prepare_dataset(root, output=None, max_side=1600, contrast='none'):
    root = Path(root).resolve()
    output = Path(output) if output else root / 'dataset'
    output.mkdir(parents=True, exist_ok=True)
    rows, seen = [], {}
    for folder in ['raw_dataset', 'batch_dataset']:
        for path in sorted((root/folder).rglob('*')):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            rel = path.relative_to(root).as_posix()
            row = dict(image_path=rel, source_group=path.parent.name if folder == 'raw_dataset' else 'batch',
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest(), pixel_hash='',
                       width=0, height=0, readable=False, duplicate_of='', split='',
                       shape_label='', color_label='', verified=False, review_status='needs_manual_review',
                       color_path='', gray_path='', scale_x=None, scale_y=None, error='')
            try:
                image = read_image(path)
                digest = hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
                row.update(readable=True, width=image.shape[1], height=image.shape[0], pixel_hash=digest)
                # Same decoded image always has the same split, even with different filenames/encodings.
                row['split'] = 'test' if int(digest[:8],16) % 5 == 0 else 'calibration'
                if digest in seen:
                    row['duplicate_of'] = seen[digest]
                    row['review_status'] = 'duplicate_excluded'
                else:
                    seen[digest] = rel
                    pre = preprocess_image(image, max_side=max_side, contrast=contrast)
                    sid = digest[:16]
                    cpath, gpath = output/'processed'/sid/'color.png', output/'processed'/sid/'gray.png'
                    write_image(cpath,pre.color)
                    write_image(gpath,pre.enhanced)
                    row.update(color_path=cpath.relative_to(output).as_posix(), gray_path=gpath.relative_to(output).as_posix(),
                               scale_x=pre.scale_x, scale_y=pre.scale_y)
            except (ValueError, OSError) as exc:
                row['error'] = str(exc)
                row['review_status'] = 'unreadable_excluded'
            rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError('Không tìm thấy ảnh trong raw_dataset hoặc batch_dataset.')
    frame.to_csv(output/'manifest.csv',index=False,encoding='utf-8-sig')
    for split in ['calibration','test']:
        frame[(frame.split==split) & frame.readable & (frame.duplicate_of=='')].to_csv(output/f'{split}_images.csv',index=False,encoding='utf-8-sig')
    report = dict(total_files=len(frame), readable=int(frame.readable.sum()),
                  duplicates=int((frame.duplicate_of!='').sum()), unique_readable=int((frame.readable & (frame.duplicate_of=='')).sum()),
                  by_source={str(k):int(v) for k,v in frame.groupby('source_group').size().items()},
                  verified_grain_labels=0,
                  note='Các nhóm Tot/Kem/Te/Vo/Tap_chat là nhãn thư mục nguồn, không phải nhãn chuẩn từng hạt. Split theo ảnh; các ảnh cùng phiên chụp cần kiểm tra và gom nhóm thủ công trước đánh giá độc lập.')
    (output/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return frame, report
