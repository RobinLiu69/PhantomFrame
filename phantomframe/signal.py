import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def find_font(font_path=None, size=60):
    if font_path:
        return ImageFont.truetype(font_path, size)
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/msjhbd.ttc", "C:/Windows/Fonts/msjh.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except (OSError, IOError):
            continue
    print("Warning: no system font found, using PIL default")
    return ImageFont.load_default()


def make_text_signal(text, canvas_size, font_size=None, font_path=None, padding=10):
    w, h = canvas_size
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    if font_size is None:
        font_size = max(10, int(h * 0.7))
        font = find_font(font_path, font_size)
        while font_size > 8:
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox[2] - bbox[0] <= w - padding * 2 and bbox[3] - bbox[1] <= h - padding * 2:
                break
            font_size -= 2
            font = find_font(font_path, font_size)
    else:
        font = find_font(font_path, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), text, fill=255, font=font)
    return img


def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size


def load_background(image_path, canvas_size, color=True):
    mode = "RGB" if color else "L"
    img = Image.open(image_path).convert(mode).resize(
        tuple(canvas_size), Image.Resampling.LANCZOS
    )
    return np.array(img, dtype=np.float32) / 255.0


def make_solid_background(canvas_size, gray=128):
    w, h = canvas_size
    return np.full((h, w), gray / 255.0, dtype=np.float32)


def make_image_signal(image_path, canvas_size):
    return Image.open(image_path).convert("L").resize(tuple(canvas_size), Image.Resampling.LANCZOS)


def apply_outline(sig_arr, width=2):
    img = Image.fromarray((sig_arr * 255).astype(np.uint8))
    eroded = img.filter(ImageFilter.MinFilter(width * 2 + 1))
    outline = np.array(img, dtype=np.float32) - np.array(eroded, dtype=np.float32)
    return np.clip(outline / 255.0, 0, 1)


def apply_density(sig_arr, density, seed=None):
    rng = np.random.default_rng(seed)
    mask = rng.random(sig_arr.shape) < density
    return sig_arr * mask.astype(np.float32)


def apply_prefilter(sig_arr, blur_radius=1.5):
    img = Image.fromarray((sig_arr * 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(blur_radius))
    return np.array(img, dtype=np.float32) / 255.0
