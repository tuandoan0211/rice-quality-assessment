"""Read and write images on Windows, including Vietnamese paths."""
from pathlib import Path
import cv2
import numpy as np

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def decode_image(data: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Không đọc được ảnh. Hãy dùng ảnh JPG, PNG, BMP hoặc TIFF hợp lệ.')
    return image


def read_image(path) -> np.ndarray:
    return decode_image(Path(path).read_bytes())


def write_image(path, image: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(path.suffix, image)
    if not ok:
        raise OSError(f'Không mã hóa được ảnh {path}')
    path.write_bytes(encoded.tobytes())
