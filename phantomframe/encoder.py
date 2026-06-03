import numpy as np
from PIL import Image, ImageFilter


def encode_random(signal, n_frames, seed=None, contrast=1.0):
    rng = np.random.default_rng(seed)
    h, w = signal.shape
    if contrast < 1.0:
        signal = 0.5 + (signal - 0.5) * contrast
    on_counts = np.round(np.clip(signal, 0, 1) * n_frames).astype(int)
    random_keys = rng.random((n_frames, h, w))
    ranks = np.argsort(np.argsort(random_keys, axis=0), axis=0)
    mask = ranks < on_counts[None, :, :]
    frames = np.zeros((n_frames, h, w), dtype=np.uint8)
    frames[mask] = 255
    return frames


def encode_bluenoise(signal, n_frames, seed=None, contrast=1.0):
    rng = np.random.default_rng(seed)
    h, w = signal.shape
    if contrast < 1.0:
        signal = 0.5 + (signal - 0.5) * contrast
    signal = np.clip(signal, 0, 1)

    y_idx, x_idx = np.meshgrid(
        np.arange(h, dtype=np.float64),
        np.arange(w, dtype=np.float64),
        indexing='ij',
    )

    frames = np.zeros((n_frames, h, w), dtype=np.uint8)
    for f in range(n_frames):
        ox = rng.uniform(0, 10000)
        oy = rng.uniform(0, 10000)
        inner = 0.06711056 * (x_idx + ox) + 0.00583715 * (y_idx + oy)
        inner = inner - np.floor(inner)
        threshold = 52.9829189 * inner
        threshold = threshold - np.floor(threshold)
        jitter = rng.random((h, w)) * 0.02
        threshold = (threshold + jitter) % 1.0
        frames[f][threshold < signal] = 255
    return frames


def encode_sparse(signal, n_frames, signal_frames, seed=None, contrast=1.0):
    rng = np.random.default_rng(seed)
    h, w = signal.shape

    boost = n_frames / signal_frames
    eff_contrast = min(1.0, contrast * boost)
    signal_mod = 0.5 + (signal - 0.5) * eff_contrast
    signal_mod = np.clip(signal_mod, 0, 1)

    step = n_frames / signal_frames
    signal_indices = {int(i * step) for i in range(signal_frames)}

    frames = np.zeros((n_frames, h, w), dtype=np.uint8)
    for f in range(n_frames):
        rand_values = rng.random((h, w))
        if f in signal_indices:
            frames[f][rand_values < signal_mod] = 255
        else:
            frames[f][rand_values < 0.5] = 255
    return frames


def _soft_mask(signal, halo):
    if halo is None or halo <= 0:
        return np.ones_like(signal)
    mask = (signal > 0.02).astype(np.uint8) * 255
    img = Image.fromarray(mask)
    img = img.filter(ImageFilter.MaxFilter(2 * int(halo) + 1))
    img = img.filter(ImageFilter.GaussianBlur(halo))
    return np.array(img, dtype=np.float32) / 255.0


def _box_blur(a, r=3):
    k = 2 * r + 1
    ap = np.pad(a, ((r, r), (0, 0)), mode="edge")
    cs = np.cumsum(ap, axis=0)
    cs = np.vstack([np.zeros((1, cs.shape[1]), cs.dtype), cs])
    a = (cs[k:, :] - cs[:-k, :]) / k
    ap = np.pad(a, ((0, 0), (r, r)), mode="edge")
    cs = np.cumsum(ap, axis=1)
    cs = np.hstack([np.zeros((cs.shape[0], 1), cs.dtype), cs])
    return (cs[:, k:] - cs[:, :-k]) / k


def _texture_mult(lum, texture, radius=3, ref=0.06, floor=0.1):
    if texture <= 0:
        return np.ones_like(lum)
    mean = _box_blur(lum, radius)
    mean_sq = _box_blur(lum * lum, radius)
    local_std = np.sqrt(np.clip(mean_sq - mean * mean, 0.0, None))
    busy = np.clip(local_std / ref, 0.0, 1.0)
    adaptive = np.clip(busy, floor, 1.0)
    return (1.0 - texture) + texture * adaptive


def encode_blend(signal, bg, n_frames, seed=None, contrast=0.3, amplitude=0.12, halo=8, texture=1.0):
    rng = np.random.default_rng(seed)
    h, w = signal.shape
    signal = np.clip(signal, 0, 1)
    is_color = bg.ndim == 3

    alpha = _soft_mask(signal, halo)

    if is_color:
        lum = np.clip(
            0.2126 * bg[:, :, 0] + 0.7152 * bg[:, :, 1] + 0.0722 * bg[:, :, 2],
            1e-6, 1.0,
        )
        max_chan = np.maximum(bg.max(axis=2), 1e-6)
        headroom = np.minimum(lum * (1.0 / max_chan - 1.0), lum)
    else:
        lum = bg
        headroom = np.minimum(bg, 1.0 - bg)

    tex = _texture_mult(lum, texture)
    grain_std = np.minimum(amplitude, headroom) * tex
    bias = signal * contrast * grain_std

    frame_shape = (n_frames, h, w, 3) if is_color else (n_frames, h, w)
    frames = np.zeros(frame_shape, dtype=np.uint8)
    for f in range(n_frames):
        grain = rng.standard_normal((h, w)) * grain_std
        delta = alpha * (bias + grain)
        if is_color:
            scale = ((lum + delta) / lum)[:, :, np.newaxis]
            frame = np.clip(bg * scale, 0.0, 1.0)
        else:
            frame = np.clip(bg + delta, 0.0, 1.0)
        frames[f] = (frame * 255).astype(np.uint8)
    return frames


def encode_partition(signal, n_frames, seed=None, contrast=1.0,
                     direction="horizontal", passive_contrast=0.0):
    rng = np.random.default_rng(seed)
    h, w = signal.shape

    sig_active = np.clip(0.5 + signal * contrast / 2, 0, 1)
    sig_passive = np.clip(0.5 + signal * passive_contrast / 2, 0, 1)

    if direction == "horizontal":
        idx_to_frame = np.arange(w) * n_frames // w
        active_template = lambda f: np.broadcast_to((idx_to_frame == f)[None, :], (h, w))
    else:
        idx_to_frame = np.arange(h) * n_frames // h
        active_template = lambda f: np.broadcast_to((idx_to_frame == f)[:, None], (h, w))

    frames = np.zeros((n_frames, h, w), dtype=np.uint8)
    for f in range(n_frames):
        active = active_template(f)
        per_pixel = np.where(active, sig_active, sig_passive)
        rand_values = rng.random((h, w))
        frames[f][rand_values < per_pixel] = 255
    return frames
