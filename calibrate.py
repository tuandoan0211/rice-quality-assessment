"""Summarize manually labeled feature ranges and estimate a same-scale whole-grain reference."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from evaluate import BOX, box_iou
from pipeline import PipelineConfig
from classification import DEFAULT_RULES
from dataclasses import asdict


def propose_reference(labels,features,capture_group):
    if not capture_group.strip():
        raise ValueError('Cần mô tả nhóm ảnh có cùng tỷ lệ chụp.')
    required=set(BOX+['verified','reviewer','shape_label','color_label'])
    if not required.issubset(labels.columns):
        raise ValueError('Nhãn thiếu cột bắt buộc; dùng grain_labels_template.csv.')
    labels=labels[labels.verified.astype(str).str.lower().isin(['true','1'])].reset_index(drop=True)
    if labels.empty or labels.reviewer.fillna('').str.strip().eq('').any():
        raise ValueError('Cần nhãn đã kiểm tra và tên người gán nhãn.')
    features=features[features.object_type=='candidate_grain'].reset_index(drop=True)
    matrix=np.array([[box_iou(a,b) for b in features[BOX].to_numpy()] for a in labels[BOX].to_numpy()]).reshape(len(labels),len(features))
    if not len(features):
        raise ValueError('Không có đặc trưng hạt hợp lệ.')
    aa,bb=linear_sum_assignment(-((matrix>=.5)*1000+matrix))
    records=[]
    for a,b in zip(aa,bb):
        if matrix[a,b]>=.5:
            records.append({**features.iloc[b].to_dict(),'manual_shape':labels.iloc[a].shape_label,'manual_color':labels.iloc[a].color_label})
    frame=pd.DataFrame(records)
    if frame.empty:
        raise ValueError('Không khớp được hộp bao giữa nhãn và đặc trưng.')
    whole=frame[(frame.manual_shape=='Nguyên') & ~frame.touches_border.astype(bool)]
    if len(whole)<5:
        raise ValueError('Cần ít nhất 5 hạt nguyên đã kiểm chứng, không cắt biên, cùng tỷ lệ chụp.')
    ref=float(whole.length.median())
    frame['length_ratio']=frame.length/ref
    ranges={}
    for axis,columns in [('manual_shape',['length','length_ratio','area','aspect_ratio']),('manual_color',['yellow_fraction','dark_fraction','mean_v'])]:
        ranges[axis]={}
        for label,group in frame.groupby(axis):
            ranges[axis][label]={'n':len(group),'features':{col:{'min':float(group[col].min()),'median':float(group[col].median()),'max':float(group[col].max())} for col in columns}}
    config=asdict(PipelineConfig(rules={**DEFAULT_RULES,'reference_length_px':ref}))
    return config,dict(capture_group=capture_group,reference_whole_grains=len(whole),reference_length_px=ref,
                       matched_labels=len(frame),ranges=ranges,
                       note='Chỉ ước lượng chiều dài chuẩn. Ngưỡng hình dạng/màu vẫn là thử nghiệm, cần điều chỉnh theo các khoảng giá trị và kiểm tra trên ảnh test cùng tỷ lệ chụp.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--labels',type=Path,required=True)
    p.add_argument('--features',type=Path,required=True)
    p.add_argument('--capture-group',required=True)
    p.add_argument('--output',type=Path,default=Path('outputs/calibration'))
    args=p.parse_args()
    labels=pd.read_csv(args.labels)
    if 'image_path' in labels and labels.image_path.nunique()>1:
        p.error('Mỗi lần dùng nhãn và đặc trưng của một ảnh cùng tỷ lệ chụp.')
    config,report=propose_reference(labels,pd.read_csv(args.features),args.capture_group)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'rules.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'ranges.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
