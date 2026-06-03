import numpy as np


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
