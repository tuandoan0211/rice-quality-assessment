"""Command-line entry point: python main.py --help."""
import argparse
import json
from pathlib import Path
from pipeline import PipelineConfig, analyze_file, export_result
from dataset_tools import prepare_dataset


def main():
    parser = argparse.ArgumentParser(description='BTL đánh giá chất lượng gạo bằng xử lý ảnh và if/else')
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare', help='Kiểm tra dữ liệu, loại trùng trong manifest và xuất hai nhánh tiền xử lý')
    prep.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    prep.add_argument('--output', type=Path)
    analyze = sub.add_parser('analyze', help='Phân tích ảnh hoặc thư mục ảnh')
    analyze.add_argument('input', type=Path)
    analyze.add_argument('--output', type=Path, default=Path('outputs/analysis'))
    analyze.add_argument('--reference-length', type=float, default=None, help='Chiều dài hạt nguyên chuẩn ở độ phân giải ảnh GỐC, px; cùng tỷ lệ chụp')
    analyze.add_argument('--config', type=Path, help='Cấu hình PipelineConfig JSON')
    analyze.add_argument('--no-watershed', action='store_true')
    analyze.add_argument('--no-texture', action='store_true')
    analyze.add_argument('--no-rois', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        _, report = prepare_dataset(args.root,args.output)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return
    values = json.loads(args.config.read_text(encoding='utf-8')) if args.config else {}
    config = PipelineConfig(**values)
    if args.reference_length is not None:
        config.rules = {**config.rules, 'reference_length_px': args.reference_length}
    if args.no_watershed:
        config.watershed=False
    if args.no_texture:
        config.texture=False
    from image_io import SUPPORTED_EXTENSIONS
    paths = sorted(p for p in args.input.rglob('*') if p.suffix.lower() in SUPPORTED_EXTENSIONS) if args.input.is_dir() else [args.input]
    if not paths:
        parser.error('Không tìm thấy ảnh đầu vào.')
    failures = 0
    for path in paths:
        try:
            result=analyze_file(path,config)
            destination = args.output/path.relative_to(args.input).with_suffix('') if args.input.is_dir() else args.output
            export_result(result,destination,path,not args.no_rois)
            print(f'{path.name}: {result.summary["total_grains"]} hạt, {result.summary["excluded_objects"]} vùng bị loại -> {destination}')
        except (ValueError,OSError) as exc:
            failures += 1
            print(f'Lỗi {path}: {exc}')
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
