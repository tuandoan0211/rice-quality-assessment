"""Generate an explicitly SYNTHETIC image with independent, known instance masks and labels."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dataclasses import asdict
import json
import cv2
import numpy as np
import pandas as pd
from image_io import write_image
from pipeline import PipelineConfig,analyze_image,export_result
from evaluate import evaluate_predictions

output=ROOT/'dataset'/'synthetic_demo'
output.mkdir(parents=True,exist_ok=True)
image=np.zeros((300,600,3),np.uint8)
recipes=[((80,80),(35,12),20,(220,220,220),'Nguyên','Bình thường'),
         ((220,80),(18,12),-15,(220,220,220),'Vỡ','Bình thường'),
         ((360,80),(35,12),40,(30,180,220),'Nguyên','Vàng'),
         ((500,80),(35,12),-20,(65,65,65),'Nguyên','Sẫm'),
         ((160,210),(18,12),10,(30,180,220),'Vỡ','Vàng')]
rows=[]
for i,(center,axes,angle,color,shape,label) in enumerate(recipes,1):
    mask=np.zeros(image.shape[:2],np.uint8)
    cv2.ellipse(mask,center,axes,angle,0,360,255,-1)
    image[mask>0]=color
    x,y,w,h=cv2.boundingRect(mask)
    rows.append(dict(image_path='dataset/synthetic_demo/scene.png',grain_id=i,bbox_x=x,bbox_y=y,bbox_w=w,bbox_h=h,
                     shape_label=shape,color_label=label,reviewer='synthetic_generator',verified=True,
                     notes='SYNTHETIC ground truth from drawing recipe; not a real-world manual label.'))
    write_image(output/f'true_mask_{i:02d}.png',mask)
write_image(output/'scene.png',image)
truth=pd.DataFrame(rows)
truth.to_csv(output/'labels.csv',index=False,encoding='utf-8-sig')
# A fixed threshold explicitly demonstrates recovery of dark grains on this synthetic black background.
config=PipelineConfig(threshold_override=30,rules={'reference_length_px':70})
(output/'config.json').write_text(json.dumps(asdict(config),indent=2),encoding='utf-8')
result=analyze_image(image,config)
export_result(result,ROOT/'outputs'/'synthetic_demo','dataset/synthetic_demo/scene.png')
report=evaluate_predictions(truth,result.classified,complete_image=True)
report['data_kind']='Synthetic five-grain scene with known labels; NOT real-image accuracy.'
(output/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
