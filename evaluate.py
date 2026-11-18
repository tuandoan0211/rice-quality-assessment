"""Compare manually verified boxes/labels to predictions by one-to-one IoU matching."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

BOX=['bbox_x','bbox_y','bbox_w','bbox_h']


def box_iou(a,b):
    ax,ay,aw,ah=map(float,a)
    bx,by,bw,bh=map(float,b)
    inter=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
    union=aw*ah+bw*bh-inter
    return inter/union if union>0 else 0.0


def evaluate_predictions(truth,predicted,complete_image=False,min_iou=.5):
    required=set(BOX+['verified','reviewer','shape_label','color_label'])
    if not required.issubset(truth.columns):
        raise ValueError(f'Nhãn cần các cột {sorted(required)}')
    verified=truth.verified.astype(str).str.lower().isin(['true','1'])
    if not verified.any():
        raise ValueError('Chưa có nhãn kiểm chứng. Không thể tính độ chính xác từ nhãn tự sinh.')
    if complete_image and not verified.all():
        raise ValueError('Đánh giá phát hiện toàn ảnh yêu cầu kiểm chứng mọi dòng nhãn.')
    gt=truth[verified].reset_index(drop=True)
    if gt.reviewer.fillna('').str.strip().eq('').any():
        raise ValueError('Mỗi nhãn kiểm chứng cần tên người gán nhãn ở cột reviewer.')
    if not gt.shape_label.isin(['Nguyên','Vỡ','Không xác định']).all() or not gt.color_label.isin(['Bình thường','Vàng','Sẫm','Không xác định']).all():
        raise ValueError('Nhãn kiểm chứng thiếu hoặc sai tên nhãn hình dạng/màu sắc.')
    if gt[BOX].isna().any().any() or (gt[['bbox_w','bbox_h']]<=0).any().any():
        raise ValueError('Hộp bao nhãn chuẩn phải hợp lệ và có kích thước dương.')
    pred=predicted[predicted.object_type=='candidate_grain'].reset_index(drop=True)
    matrix=np.array([[box_iou(a,b) for b in pred[BOX].to_numpy()] for a in gt[BOX].to_numpy()]).reshape(len(gt),len(pred))
    score=(matrix>=min_iou).astype(float)*1000+matrix
    pairs=[]
    if len(gt) and len(pred):
        aa,bb=linear_sum_assignment(-score)
        pairs=[(a,b) for a,b in zip(aa,bb) if matrix[a,b]>=min_iou]
    report=dict(verified_truth_grains=len(gt),predicted_grains=len(pred),matched_grains=len(pairs),min_box_iou=min_iou,
                complete_image=bool(complete_image),mean_matched_box_iou=float(np.mean([matrix[a,b] for a,b in pairs])) if pairs else None,
                classification_scope='Độ chính xác chỉ trên hạt đã khớp hộp bao, không bao gồm hạt bỏ sót.')
    confusion={}
    for axis in ['shape_label','color_label']:
        records=[{'truth':gt.iloc[a][axis],'prediction':pred.iloc[b][axis]} for a,b in pairs]
        report[f'{axis}_accuracy']=sum(r['truth']==r['prediction'] for r in records)/len(records) if records else None
        confusion[axis]=pd.crosstab(pd.Series([r['truth'] for r in records],name='truth'),pd.Series([r['prediction'] for r in records],name='prediction')).to_dict()
    if complete_image:
        tp=len(pairs)
        report.update(detection_precision=tp/len(pred) if len(pred) else 0.0,detection_recall=tp/len(gt),
                      missed_grains=len(gt)-tp,extra_regions=len(pred)-tp,count_absolute_error=abs(len(gt)-len(pred)))
    else:
        report['detection_note']='Chưa xác nhận gán nhãn hết ảnh; không tính precision/recall và sai số đếm.'
    report['confusion']=confusion
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--labels',type=Path,required=True)
    p.add_argument('--predictions',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('outputs/evaluation.json'))
    p.add_argument('--complete-image',action='store_true',help='Xác nhận đã gán nhãn TẤT CẢ hạt của một ảnh, gồm hạt thuật toán bỏ sót')
    args=p.parse_args()
    truth=pd.read_csv(args.labels)
    if 'image_path' in truth and truth.image_path.nunique()>1:
        p.error('Mỗi lần đánh giá một ảnh; không trộn nhiều ảnh trong cùng CSV.')
    report=evaluate_predictions(truth,pd.read_csv(args.predictions),args.complete_image)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
