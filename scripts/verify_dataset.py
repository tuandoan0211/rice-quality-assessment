"""Run the pipeline over every supplied image and persist runtime checks, not accuracy claims."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import time
import numpy as np
import pandas as pd
from image_io import SUPPORTED_EXTENSIONS
from pipeline import analyze_file, export_result


def main(export_examples=False):
    output=ROOT/'outputs'/'verification'
    output.mkdir(parents=True,exist_ok=True)
    paths=sorted(p for folder in ['raw_dataset','batch_dataset'] for p in (ROOT/folder).rglob('*') if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    rows=[]
    all_features=[]
    all_predictions=[]
    for i,path in enumerate(paths,1):
        start=time.perf_counter()
        try:
            result=analyze_file(path)
            assert len(result.features)==len(result.classified)==len(result.segmentation.regions)
            assert result.summary['total_grains']+result.summary['excluded_objects']==result.summary['detected_regions']
            if result.summary['total_grains']:
                for _,group in result.distribution.groupby('group'):
                    assert abs(group.percentage.sum()-100)<1e-6
                assert np.isfinite(result.features[['area','length','width','mean_v','yellow_fraction','dark_fraction']].to_numpy()).all()
            row=dict(image_path=path.relative_to(ROOT).as_posix(),success=True,**result.summary,
                     seconds=time.perf_counter()-start,error='')
            for frame,collection in [(result.features,all_features),(result.classified,all_predictions)]:
                copy=frame.copy()
                copy.insert(0,'image_path',path.relative_to(ROOT).as_posix())
                collection.append(copy)
            # Full exports for one image of each source type, plus the first two batch images.
            if export_examples and path.name in {'picT (1).png','picV (1).png','picK (1).png','picTe (1).png','picTC (1).png','picCacloaigao (1).jpg','picCacloaigao (10).jpg'}:
                export_result(result,ROOT/'outputs'/'examples'/path.parent.name/path.stem,path,export_rois=True)
        except Exception as exc:
            row=dict(image_path=path.relative_to(ROOT).as_posix(),success=False,seconds=time.perf_counter()-start,error=repr(exc))
        rows.append(row)
        print(f'{i}/{len(paths)} {path.name}: {row["success"]}',flush=True)
    pd.DataFrame(rows).to_csv(output/'all_images.csv',index=False,encoding='utf-8-sig')
    if all_features:
        features=pd.concat(all_features,ignore_index=True)
        features.to_csv(output/'all_features.csv',index=False,encoding='utf-8-sig')
        pd.concat(all_predictions,ignore_index=True).to_csv(output/'all_classification.csv',index=False,encoding='utf-8-sig')
        labels=features[['image_path','grain_id','bbox_x','bbox_y','bbox_w','bbox_h']].copy()
        for col in ['shape_label','color_label','reviewer','notes']:
            labels[col]=''
        labels['verified']=False
        if not (output/'all_grain_labels_template.csv').exists():
            labels.to_csv(output/'all_grain_labels_template.csv',index=False,encoding='utf-8-sig')
    report=dict(total=len(rows),passed=sum(r['success'] for r in rows),failed=sum(not r['success'] for r in rows),
                kind='Runtime and consistency verification; NOT real-world detection/classification accuracy.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report['failed']:
        raise SystemExit(1)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-examples',action='store_true',help='Xuất thêm ảnh mẫu và ROI; mặc định chỉ lưu các bảng kiểm tra.')
    args=parser.parse_args()
    main(export_examples=args.export_examples)
