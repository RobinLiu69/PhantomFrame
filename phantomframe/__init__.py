from .encoder import encode_random, encode_bluenoise, encode_sparse, encode_partition, encode_blend
from .signal import (
    make_text_signal,
    make_image_signal,
    get_image_size,
    load_background,
    make_solid_background,
    apply_outline,
    apply_density,
    apply_prefilter,
)
from .preview import make_preview_gif, save_outputs

__version__ = "4.0.0"
__all__ = [
    "encode_random",
    "encode_bluenoise",
    "encode_sparse",
    "encode_partition",
    "encode_blend",
    "make_text_signal",
    "make_image_signal",
    "get_image_size",
    "load_background",
    "make_solid_background",
    "apply_outline",
    "apply_density",
    "apply_prefilter",
    "make_preview_gif",
    "save_outputs",
]
