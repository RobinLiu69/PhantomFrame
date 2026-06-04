import warnings

import numpy as np
import pytest

from phantomframe import (
    encode_random,
    encode_bluenoise,
    encode_sparse,
    encode_blend,
    make_text_signal,
    make_solid_background,
    apply_outline,
    apply_density,
    apply_prefilter,
)


def test_encode_random_reconstructs_signal():
    rng = np.random.default_rng(0)
    signal = rng.random((16, 16)).astype(np.float32)
    n = 256
    frames = encode_random(signal, n, seed=1, contrast=1.0)

    recon = frames.mean(axis=0) / 255.0
    assert np.max(np.abs(recon - signal)) <= 0.5 / n + 1e-6


def test_encode_random_is_binary():
    frames = encode_random(np.full((8, 8), 0.5, np.float32), 10, seed=0)
    assert frames.dtype == np.uint8
    assert set(np.unique(frames)).issubset({0, 255})


def test_encode_random_extremes():
    signal = np.array([[0.0, 1.0]], dtype=np.float32)
    frames = encode_random(signal, 12, seed=0)
    assert np.all(frames[:, 0, 0] == 0)
    assert np.all(frames[:, 0, 1] == 255)


def test_encode_bluenoise_reconstructs_signal():
    signal = np.full((24, 24), 0.4, np.float32)
    n = 3000
    frames = encode_bluenoise(signal, n, seed=2, contrast=1.0)

    recon = frames.mean(axis=0) / 255.0
    assert abs(recon.mean() - 0.4) < 0.02
    assert np.mean(np.abs(recon - signal)) < 0.03


def test_encode_bluenoise_is_binary():
    frames = encode_bluenoise(np.full((8, 8), 0.5, np.float32), 5, seed=0)
    assert set(np.unique(frames)).issubset({0, 255})


def _block_signal(h, w, top, bottom, left, right):
    sig = np.zeros((h, w), dtype=np.float32)
    sig[top:bottom, left:right] = 1.0
    return sig


def test_encode_blend_grain_is_zero_mean_off_signal():
    h, w = 80, 80
    bg_val = 128 / 255.0
    bg = make_solid_background((w, h), gray=128)
    sig = _block_signal(h, w, 30, 50, 30, 50)
    n = 800
    frames = encode_blend(sig, bg, n, seed=3, contrast=0.3,
                          amplitude=0.12, halo=4, texture=0.0)

    avg = frames.mean(axis=0) / 255.0
    corner = avg[:10, :10]
    assert np.allclose(corner, bg_val, atol=1e-6)
    off = sig < 0.5
    assert np.mean(np.abs(avg[off] - bg_val)) < 0.01


def test_encode_blend_signal_offset_emerges():
    h, w = 80, 80
    bg_val = 128 / 255.0
    bg = make_solid_background((w, h), gray=128)
    sig = _block_signal(h, w, 25, 55, 25, 55)
    contrast, amplitude = 0.3, 0.12
    n = 1500
    frames = encode_blend(sig, bg, n, seed=4, contrast=contrast,
                          amplitude=amplitude, halo=8, texture=0.0)

    avg = frames.mean(axis=0) / 255.0
    interior = avg[38:42, 38:42]
    expected = bg_val + 1.0 * contrast * amplitude
    assert np.allclose(interior.mean(), expected, atol=0.01)


def test_encode_blend_color_shape_and_range():
    h, w = 40, 40
    bg = np.full((h, w, 3), 0.5, dtype=np.float32)
    sig = _block_signal(h, w, 10, 30, 10, 30)
    frames = encode_blend(sig, bg, 6, seed=0, contrast=0.3)
    assert frames.shape == (6, h, w, 3)
    assert frames.dtype == np.uint8
    assert frames.min() >= 0 and frames.max() <= 255


def test_encode_sparse_warns_on_saturation():
    sig = np.full((8, 8), 0.7, np.float32)
    with pytest.warns(UserWarning, match="saturated"):
        encode_sparse(sig, n_frames=10, signal_frames=2, seed=0, contrast=0.4)


def test_encode_sparse_no_warning_when_within_budget():
    sig = np.full((8, 8), 0.7, np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        encode_sparse(sig, n_frames=10, signal_frames=5, seed=0, contrast=0.4)


def _sample_signal(h=30, w=30):
    sig = np.zeros((h, w), dtype=np.float32)
    sig[8:22, 8:22] = 1.0
    return sig


def test_apply_outline_shape_and_range():
    sig = _sample_signal()
    out = apply_outline(sig, width=2)
    assert out.shape == sig.shape
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert out.max() > 0.0
    assert out.sum() < sig.sum()


def test_apply_density_shape_and_range():
    sig = _sample_signal()
    out = apply_density(sig, density=0.3, seed=0)
    assert out.shape == sig.shape
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert np.count_nonzero(out) < np.count_nonzero(sig)


def test_apply_density_full_keeps_everything():
    sig = _sample_signal()
    out = apply_density(sig, density=1.0, seed=0)
    assert np.array_equal(out, sig)


def test_apply_prefilter_shape_and_range():
    sig = _sample_signal()
    out = apply_prefilter(sig, blur_radius=1.5)
    assert out.shape == sig.shape
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_make_text_signal_size_and_nonblank():
    canvas = (200, 80)
    img = make_text_signal("Hi", canvas)
    assert img.size == canvas
    arr = np.array(img)
    assert arr.max() > 0
