"""Local Streamlit demo: python -m streamlit run app.py"""
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
import hashlib
import json
import zipfile
import cv2
import streamlit as st
from image_io import decode_image
from pipeline import PipelineConfig, analyze_image
from rice_statistics import create_statistics_figure

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Đánh giá chất lượng gạo', page_icon='🌾', layout='wide')
st.title('Đánh giá chất lượng gạo bằng xử lý ảnh')
st.caption('BTL · Otsu và Watershed · Hình dạng, RGB/HSV, GLCM · Phân loại if/else')
with st.sidebar:
    st.header('Ảnh đầu vào')
    upload = st.file_uploader('Tải ảnh gạo', type=['jpg','jpeg','png','bmp','tif','tiff','webp'])
    examples = sorted([*ROOT.glob('raw_dataset/*/*'), *ROOT.glob('batch_dataset/*'), *ROOT.glob('dataset/synthetic_demo/scene.png')])
    sample = st.selectbox('Hoặc chọn ảnh có sẵn', [str(p.relative_to(ROOT)) for p in examples if p.is_file()])
    demo = 'synthetic_demo' in sample and upload is None
    st.header('Phân đoạn')
    max_side=st.select_slider('Cạnh dài tối đa (px)',[800,1200,1600,2000],value=1600)
    contrast=st.selectbox('Cải thiện tương phản',['none','clahe','equalize'],format_func=lambda x:{'none':'Giữ nguyên','clahe':'CLAHE','equalize':'Cân bằng histogram'}[x])
    foreground=st.selectbox('Hạt so với nền',['auto','bright','dark'],format_func=lambda x:{'auto':'Tự động theo biên ảnh','bright':'Hạt sáng trên nền tối','dark':'Hạt tối trên nền sáng'}[x])
    min_area=st.number_input('Diện tích vùng tối thiểu (px ảnh xử lý)',1,10000,12)
    use_manual_threshold=st.checkbox('Dùng ngưỡng thủ công khi Otsu bỏ sót hạt tối',demo)
    threshold=st.slider('Ngưỡng phân đoạn thủ công',0,255,30) if use_manual_threshold else None
    watershed=st.checkbox('Tách vùng tiếp xúc bằng Watershed',True)
    exclude=st.checkbox('Loại vùng rất lớn và gần tròn',True,help='Bộ lọc hình học dành cho đồng xu/vật lớn; vẫn cần kiểm tra ảnh kết quả.')
    texture=st.checkbox('Tính đặc trưng GLCM',True)
    st.header('Quy tắc hình dạng')
    ref=st.number_input('Chiều dài hạt nguyên chuẩn (px ảnh gốc)',min_value=0.0,value=70.0 if demo else 0.0,step=1.0,
                        help='Đo hạt nguyên đã biết, cùng giống và tỷ lệ chụp. Giá trị 0 để nhãn hình dạng là Không xác định.')
    broken=st.slider('Vỡ nếu tỷ lệ chiều dài nhỏ hơn',0.10,0.90,0.70,0.01)
    whole=st.slider('Nguyên nếu tỷ lệ chiều dài từ',0.20,1.20,0.80,0.01)
    st.header('Quy tắc màu thử nghiệm')
    yellow=st.slider('Tỷ lệ pixel vàng để gán nhãn Vàng',0.11,1.0,0.25,0.01)
    dark=st.slider('Tỷ lệ pixel sẫm để gán nhãn Sẫm',0.11,1.0,0.30,0.01)
    with st.expander('Ngưỡng pixel trong HSV'):
        hue=st.slider('Khoảng H của pixel vàng (OpenCV)',0,179,(10,40))
        sat=st.slider('S tối thiểu của pixel vàng',0,255,55)
        value=st.slider('V tối thiểu của pixel vàng',0,255,65)
        dark_v=st.slider('V tối đa của pixel sẫm',0,255,85)

config=PipelineConfig(max_side=max_side,contrast=contrast,foreground=foreground,min_area=int(min_area),
    threshold_override=threshold,
    watershed=watershed,texture=texture,exclude_large_round=exclude,
    rules=dict(reference_length_px=ref or None,broken_max=broken,whole_min=whole,yellow_min_fraction=yellow,dark_min_fraction=dark),
    color_rules=dict(yellow_h_min=hue[0],yellow_h_max=hue[1],yellow_s_min=sat,yellow_v_min=value,dark_v_max=dark_v))


@st.cache_data(show_spinner=False,max_entries=8)
def run_analysis(data,values):
    return analyze_image(decode_image(data),PipelineConfig(**values))


try:
    data=upload.getvalue() if upload else (ROOT/sample).read_bytes()
    source_name=upload.name if upload else sample
    with st.spinner('Đang tách hạt và đo đặc trưng…'):
        result=run_analysis(data,asdict(config))
except (ValueError,OSError) as exc:
    st.error(str(exc))
    st.stop()
st.write(f'Ảnh đang phân tích: **{source_name}**')
if demo:
    st.info('Ảnh tổng hợp 5 hạt, chiều dài chuẩn 70 px và ngưỡng phân đoạn 30. Chỉ dùng minh họa chức năng; không đại diện độ chính xác trên ảnh thật.')
for warning in result.warnings:
    st.warning(warning)
cols=st.columns(4)
for col,title,key in zip(cols,['Hạt ứng viên','Vùng bị loại','Hạt chưa xác định','Dài trung bình (px gốc)'],
                        ['total_grains','excluded_objects','unknown_grains','mean_length_px']):
    val=result.summary[key]
    col.metric(title,f'{val:.1f}' if isinstance(val,float) else val if val is not None else '—')
tabs=st.tabs(['Các bước xử lý','Kết quả và thống kê','Gán nhãn đối chiếu','Hướng dẫn'])
with tabs[0]:
    a,b=st.columns(2)
    a.image(cv2.cvtColor(decode_image(data),cv2.COLOR_BGR2RGB),caption='Ảnh gốc',width='stretch')
    b.image(result.preprocessing.gray,caption='Ảnh xám sau resize giữ tỷ lệ',width='stretch')
    a.image(result.preprocessing.enhanced,caption=f'Gaussian và tương phản: {contrast}',width='stretch')
    method='thủ công' if threshold is not None else 'Otsu'
    b.image(result.segmentation.binary,caption=f'Mask {method}: {result.segmentation.threshold:.1f}; tiền cảnh: {result.segmentation.foreground}',width='stretch')
    st.image(cv2.cvtColor(result.annotated,cv2.COLOR_BGR2RGB),caption='ID và nhãn · N nguyên · V vỡ · BT bình thường · Y vàng · S sẫm · ? chưa xác định · X vùng loại',width='stretch')
with tabs[1]:
    st.dataframe(result.classified,width='stretch',hide_index=True)
    figure=create_statistics_figure(result.distribution)
    st.pyplot(figure)
    import matplotlib.pyplot as plt
    plt.close(figure)
    st.dataframe(result.distribution,width='stretch',hide_index=True)
    st.caption('Mỗi trục hình dạng hoặc màu sắc cộng thành 100%. Một hạt có thể vừa vỡ vừa vàng; không cộng hai trục với nhau.')
    st.download_button('Tải bảng phân loại CSV',result.classified.to_csv(index=False).encode('utf-8-sig'),'classification.csv','text/csv')
    buffer=BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for name,frame in [('features',result.features),('classification',result.classified),('statistics',result.distribution)]:
            z.writestr(f'{name}.csv',frame.to_csv(index=False).encode('utf-8-sig'))
        z.writestr('summary.json',json.dumps(dict(summary=result.summary,warnings=result.warnings,config=asdict(config)),ensure_ascii=False,indent=2))
        for name,array in [('annotated',result.annotated),('mask',result.segmentation.binary)]:
            z.writestr(f'{name}.png',cv2.imencode('.png',array)[1].tobytes())
    st.download_button('Tải gói kết quả ZIP',buffer.getvalue(),'rice_results.zip','application/zip')
    st.download_button('Tải cấu hình hiện tại',json.dumps(asdict(config),ensure_ascii=False,indent=2),'rules.json','application/json')
with tabs[2]:
    st.write('Kiểm tra ID trên ảnh, sửa hộp bao nếu cần và tự gán hai nhãn. Thêm dòng cho hạt bị bỏ sót; xóa vùng không phải hạt. Chỉ đánh dấu verified sau khi kiểm tra thủ công.')
    st.image(cv2.cvtColor(result.annotated,cv2.COLOR_BGR2RGB),width='stretch')
    template=result.features[['grain_id','bbox_x','bbox_y','bbox_w','bbox_h']].copy()
    template.insert(0,'image_path',source_name)
    for col in ['shape_label','color_label','reviewer','notes']:
        template[col]=''
    template['verified']=False
    editor_key='labels_'+hashlib.sha256(data+json.dumps(asdict(config),sort_keys=True).encode()).hexdigest()[:20]
    edited=st.data_editor(template,num_rows='dynamic',hide_index=True,width='stretch',key=editor_key,
        column_config={'shape_label':st.column_config.SelectboxColumn('Hình dạng',options=['','Nguyên','Vỡ','Không xác định']),
                       'color_label':st.column_config.SelectboxColumn('Màu sắc',options=['','Bình thường','Vàng','Sẫm','Không xác định']),
                       'verified':st.column_config.CheckboxColumn('Đã kiểm chứng')})
    st.download_button('Tải nhãn thủ công CSV',edited.to_csv(index=False).encode('utf-8-sig'),'grain_labels.csv','text/csv')
    st.caption('Nhãn đang sửa chỉ nằm trong phiên trình duyệt. Tải CSV để lưu trước khi thay ảnh hoặc cấu hình. Không dùng dự đoán làm nhãn chuẩn.')
with tabs[3]:
    st.markdown('''1. Chọn ảnh chụp từ trên xuống, ánh sáng ổn định và nền tương phản.
2. Kiểm tra mask trước khi đọc kết quả. Thử đổi tương phản, diện tích tối thiểu và Watershed nếu cần.
3. Đo chiều dài một nhóm hạt nguyên đã biết ở ảnh gốc; nhập trung vị làm chuẩn chỉ khi cùng tỷ lệ chụp.
4. Hiệu chỉnh ngưỡng bằng dữ liệu calibration, sau đó cố định cấu hình để đánh giá ảnh test.
5. Xuất CSV và gán nhãn thủ công để đối chiếu.

Diện tích, chu vi, chiều dài/rộng được quy về pixel ảnh gốc; không phải mm. RGB/HSV lấy bên trong mask từ ảnh màu chưa cân bằng histogram. GLCM chỉ tính cặp pixel nằm trong hạt. Chưa kết luận được hạt lép, độ ẩm, an toàn thực phẩm hay cấp chất lượng thương mại từ ảnh này.''')
