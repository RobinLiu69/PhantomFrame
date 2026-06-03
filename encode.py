import argparse
import numpy as np

from arg_encoder import (
    encode_random, encode_bluenoise, encode_sparse, encode_partition,
    make_text_signal, make_image_signal,
    apply_outline, apply_density, apply_prefilter,
    save_outputs,
)


def build_parser():
    p = argparse.ArgumentParser(
        description="ARG Temporal Dithering Encoder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text",  help="text to hide")
    src.add_argument("--image", help="image path to hide (grayscale)")

    p.add_argument("-n", "--frames",     type=int, default=6,     help="number of output frames (default: 6)")
    p.add_argument("-o", "--output-dir", default="output",        help="output directory (default: output/)")
    p.add_argument("--canvas",           type=int, nargs=2,
                   metavar=("W", "H"),   default=(400, 150),      help="canvas size (default: 400 150)")
    p.add_argument("--contrast",         type=float, default=0.4, help="signal contrast 0-1 (default: 0.4)")
    p.add_argument("--invert",           action="store_true",     help="invert signal")
    p.add_argument("--font-size",        type=int, default=None,  help="font size (default: auto)")
    p.add_argument("--font",             default=None,            help="font file path")
    p.add_argument("--seed",             type=int,                help="random seed for reproducibility")
    p.add_argument("--preview-gif",      action="store_true",     help="output animated GIF preview")
    p.add_argument("--preview-fps",      type=int, default=24,   help="GIF frame rate (default: 24)")

    p.add_argument(
        "--method",
        choices=["random", "bluenoise", "sparse", "partition"],
        default="bluenoise",
        help="encoding algorithm (default: bluenoise)",
    )
    p.add_argument("--signal-frames",    type=int, default=None,
                   help="(sparse) number of frames carrying the signal")
    p.add_argument("--direction",
                   choices=["horizontal", "vertical"], default="horizontal",
                   help="(partition) strip direction (default: horizontal)")
    p.add_argument("--passive-contrast", type=float, default=0.0,
                   help="(partition) contrast of inactive strips (default: 0)")

    p.add_argument("--outline",          action="store_true",     help="outline-only mode")
    p.add_argument("--outline-width",    type=int, default=2,     help="outline width (default: 2)")
    p.add_argument("--density",          type=float, default=1.0, help="signal pixel density 0-1 (default: 1.0)")
    p.add_argument("--prefilter",        action="store_true",     help="Gaussian blur before encoding")
    p.add_argument("--blur",             type=float, default=1.5, help="blur radius (default: 1.5)")

    return p


def main():
    p = build_parser()
    args = p.parse_args()

    if args.text:
        sig = make_text_signal(args.text, tuple(args.canvas),
                               font_size=args.font_size, font_path=args.font)
    else:
        sig = make_image_signal(args.image, tuple(args.canvas))

    sig_arr = np.array(sig, dtype=np.float32) / 255.0
    if args.invert:
        sig_arr = 1.0 - sig_arr
    if args.outline:
        sig_arr = apply_outline(sig_arr, width=args.outline_width)
    if args.density < 1.0:
        sig_arr = apply_density(sig_arr, args.density, seed=args.seed)
    if args.prefilter:
        sig_arr = apply_prefilter(sig_arr, blur_radius=args.blur)

    if args.method == "sparse":
        sf = args.signal_frames
        if sf is None or not (1 <= sf <= args.frames):
            p.error(f"--method sparse requires --signal-frames between 1 and {args.frames}")
        frames = encode_sparse(sig_arr, args.frames, sf,
                               seed=args.seed, contrast=args.contrast)
    elif args.method == "partition":
        frames = encode_partition(sig_arr, args.frames,
                                  seed=args.seed, contrast=args.contrast,
                                  direction=args.direction,
                                  passive_contrast=args.passive_contrast)
    elif args.method == "bluenoise":
        frames = encode_bluenoise(sig_arr, args.frames,
                                  seed=args.seed, contrast=args.contrast)
    else:
        frames = encode_random(sig_arr, args.frames,
                               seed=args.seed, contrast=args.contrast)

    out_dir = save_outputs(frames, sig_arr, args.output_dir,
                           gif=args.preview_gif, gif_fps=args.preview_fps)
    print(f"Done: {args.frames} frames saved to {out_dir}/ (method: {args.method})")


if __name__ == "__main__":
    main()
