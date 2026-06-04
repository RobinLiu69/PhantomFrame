import argparse
import numpy as np

from . import (
    encode_random, encode_bluenoise, encode_sparse, encode_partition, encode_blend,
    make_text_signal, make_image_signal,
    get_image_size, load_background, make_solid_background,
    apply_outline, apply_density, apply_prefilter,
    save_outputs,
)


def build_parser():
    p = argparse.ArgumentParser(
        prog="phantomframe",
        description="phantomframe - hide a message in frame noise or blend it into a photo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text",  help="text to hide")
    src.add_argument("--image", help="image path to hide (grayscale)")

    p.add_argument("-n", "--frames",     type=int, default=6,     help="number of output frames (default: 6)")
    p.add_argument("-o", "--output-dir", default="output",        help="output directory (default: output/)")
    p.add_argument("--canvas",           type=int, nargs=2,
                   metavar=("W", "H"),   default=None,
                   help="canvas size (default: bg image size if --bg given, else 400 150)")
    p.add_argument("--contrast",         type=float, default=None,
                   help="signal strength 0-1 (default: 0.4 for noise methods; "
                        "for blend it is the signal/grain ratio, default 0.3)")
    p.add_argument("--invert",           action="store_true",     help="invert signal")
    p.add_argument("--font-size",        type=int, default=None,  help="font size (default: auto)")
    p.add_argument("--font",             default=None,            help="font file path")
    p.add_argument("--seed",             type=int,                help="random seed for reproducibility")
    p.add_argument("--preview-gif",      action="store_true",     help="output animated GIF preview")
    p.add_argument("--preview-fps",      type=int, default=24,   help="GIF frame rate (default: 24)")

    p.add_argument(
        "--method",
        choices=["random", "bluenoise", "sparse", "partition"],
        default="random",
        help="encoding algorithm (default: random). 'bluenoise' is IGN-based "
             "temporal dithering, visually close to but not true blue noise.",
    )
    p.add_argument("--bg",        default=None,
                   help="background image path; hides the signal inside the photo")
    p.add_argument("--bg-color",  type=int, default=None,
                   help="solid background gray value 0-255; hides the signal in a solid colour block")
    p.add_argument("--amplitude", type=float, default=0.12,
                   help="(blend) per-frame gaussian grain depth 0-1 (default: 0.12). "
                        "Higher = better single-frame hiding but noisier frames.")
    p.add_argument("--halo",      type=int, default=8,
                   help="(blend) soft noise-halo radius in px around the text (default: 8). "
                        "0 = grain the whole frame.")
    p.add_argument("--texture",   type=float, default=1.0,
                   help="(blend) adapt grain to local detail 0-1 (default: 1.0). "
                        "Keeps flat single-colour areas quiet; 0 = uniform grain.")
    p.add_argument("--signal-frames",    type=int, default=None,
                   help="(sparse) number of frames carrying the signal. "
                        "Too small saturates the contrast and the average can't "
                        "fully restore brightness; use >= contrast * frames.")
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

    density_seed, encoder_seed = np.random.SeedSequence(args.seed).spawn(2)

    canvas = tuple(args.canvas) if args.canvas else \
             (get_image_size(args.bg) if args.bg else (400, 150))

    if args.text:
        sig = make_text_signal(args.text, canvas,
                               font_size=args.font_size, font_path=args.font)
    else:
        sig = make_image_signal(args.image, canvas)

    sig_arr = np.array(sig, dtype=np.float32) / 255.0
    if args.invert:
        sig_arr = 1.0 - sig_arr
    if args.outline:
        sig_arr = apply_outline(sig_arr, width=args.outline_width)
    if args.density < 1.0:
        sig_arr = apply_density(sig_arr, args.density, seed=density_seed)
    if args.prefilter:
        sig_arr = apply_prefilter(sig_arr, blur_radius=args.blur)

    use_blend = args.bg is not None or args.bg_color is not None

    if args.contrast is None:
        args.contrast = 0.3 if use_blend else 0.4

    if use_blend:
        bg = load_background(args.bg, canvas, color=True) if args.bg \
            else make_solid_background(canvas, gray=args.bg_color)
        frames = encode_blend(sig_arr, bg, args.frames,
                              seed=encoder_seed, contrast=args.contrast,
                              amplitude=args.amplitude, halo=args.halo,
                              texture=args.texture)
    elif args.method == "sparse":
        sf = args.signal_frames
        if sf is None or not (1 <= sf <= args.frames):
            p.error(f"--method sparse requires --signal-frames between 1 and {args.frames}")
        if sf == args.frames:
            print("Info: sparse with signal-frames == frames is equivalent to random mode "
                  "(every frame carries the signal, no decoy frames).")
        frames = encode_sparse(sig_arr, args.frames, sf,
                               seed=encoder_seed, contrast=args.contrast)
    elif args.method == "partition":
        frames = encode_partition(sig_arr, args.frames,
                                  seed=encoder_seed, contrast=args.contrast,
                                  direction=args.direction,
                                  passive_contrast=args.passive_contrast)
    elif args.method == "bluenoise":
        frames = encode_bluenoise(sig_arr, args.frames,
                                  seed=encoder_seed, contrast=args.contrast)
    else:
        frames = encode_random(sig_arr, args.frames,
                               seed=encoder_seed, contrast=args.contrast)

    out_dir = save_outputs(frames, sig_arr, args.output_dir,
                           gif=args.preview_gif, gif_fps=args.preview_fps)
    mode = "blend" if use_blend else args.method
    print(f"Done: {args.frames} frames saved to {out_dir}/ (mode: {mode})")


if __name__ == "__main__":
    main()
