from pathlib import Path
import numpy as np
from PIL import Image


def make_preview_gif(frames, out_path, fps=24):
    duration = int(1000 / fps)
    pil = [Image.fromarray(f) for f in frames]
    pil[0].save(
        out_path,
        save_all=True,
        append_images=pil[1:],
        duration=duration,
        loop=0,
        optimize=False,
    )


def save_outputs(frames, sig_arr, out_dir, gif=False, gif_fps=24):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        Image.fromarray(frame).save(out_dir / f"frame_{i + 1:02d}.png")

    avg = frames.mean(axis=0).astype(np.uint8)
    Image.fromarray(avg).save(out_dir / "_preview_average.png")
    Image.fromarray((sig_arr * 255).astype(np.uint8)).save(out_dir / "_signal_processed.png")

    if gif:
        make_preview_gif(frames, out_dir / "_preview_animation.gif", fps=gif_fps)

    return out_dir
