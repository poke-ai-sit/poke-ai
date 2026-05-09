# sprite_gen/process.py
"""
Convert a side-by-side FRONT/BACK generated image into two 64x64 indexed PNGs
and a shared JASC-PAL palette file, ready for pokefirered/graphics/pokemon/<name>/.

GBA sprites share one 16-color palette between front and back. This script
builds a unified palette from both halves before quantizing, so both sprites
use the same color indices.
"""

from pathlib import Path
from PIL import Image


def _build_unified_palette(regions: list[Image.Image]) -> list[int]:
    """
    Quantize all regions together to produce a shared 16-color palette.
    Returns a flat palette list [R0,G0,B0, R1,G1,B1, ...] with 16 entries,
    white guaranteed at index 0.
    """
    # Concatenate all regions side-by-side into one wide image for joint quantization
    total_w = sum(r.width for r in regions)
    max_h = max(r.height for r in regions)
    combined = Image.new("RGB", (total_w, max_h), (255, 255, 255))
    x = 0
    for r in regions:
        combined.paste(r, (x, 0))
        x += r.width

    quantized = combined.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:16 * 3]  # first 16 RGB entries

    # Ensure white (#FFFFFF or close) is at index 0
    white_idx = None
    for i in range(16):
        r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        if r >= 248 and g >= 248 and b >= 248:
            white_idx = i
            break

    if white_idx is not None and white_idx != 0:
        for ch in range(3):
            palette[ch], palette[white_idx * 3 + ch] = (
                palette[white_idx * 3 + ch],
                palette[ch],
            )

    return palette


def _apply_palette(region: Image.Image, palette: list[int]) -> Image.Image:
    """Re-quantize a region using a fixed pre-built palette."""
    # Build a palette image to use as the quantization target
    pal_img = Image.new("P", (1, 1))
    full_palette = palette + [0] * (768 - len(palette))
    pal_img.putpalette(full_palette)
    quantized = region.quantize(palette=pal_img, dither=0)
    return quantized


def write_jasc_pal(palette: list[int], pal_path: Path) -> None:
    """Write JASC-PAL file from a flat palette list [R,G,B, ...]."""
    with open(pal_path, "w", newline="\n") as f:
        f.write("JASC-PAL\n0100\n16\n")
        for i in range(16):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            f.write(f"{r} {g} {b}\n")


def _flatten_alpha(img: Image.Image) -> Image.Image:
    """Paste RGBA image onto a white RGB background."""
    bg = Image.new("RGB", img.size, (255, 255, 255))
    if img.mode == "RGBA":
        bg.paste(img, mask=img.split()[3])
    else:
        bg.paste(img)
    return bg


def process_sprite(
    source_path: Path,
    front_png: Path,
    back_png: Path,
    pal_path: Path,
    front_crop: tuple[int, int, int, int] | None = None,
    back_crop: tuple[int, int, int, int] | None = None,
) -> None:
    """
    Crop, resize, quantize a side-by-side sprite image and write outputs.

    front_crop / back_crop: (left, upper, right, lower) pixel boxes.
    If None, the image is split down the centre and the bottom 15% is
    treated as label area and excluded.
    """
    img = Image.open(source_path).convert("RGBA")
    w, h = img.size

    if front_crop is None:
        label_h = int(h * 0.15)
        front_crop = (0, 0, w // 2, h - label_h)
    if back_crop is None:
        label_h = int(h * 0.15)
        back_crop = (w // 2, 0, w, h - label_h)

    # Crop and flatten to RGB
    front_rgb = _flatten_alpha(img.crop(front_crop)).resize((64, 64), Image.NEAREST)
    back_rgb = _flatten_alpha(img.crop(back_crop)).resize((64, 64), Image.NEAREST)

    # Build shared palette from both sprites
    palette = _build_unified_palette([front_rgb, back_rgb])

    # Apply shared palette to each sprite
    front_indexed = _apply_palette(front_rgb, palette)
    back_indexed = _apply_palette(back_rgb, palette)

    front_indexed.save(front_png)
    back_indexed.save(back_png)
    write_jasc_pal(palette, pal_path)

    print(f"Wrote {front_png}")
    print(f"Wrote {back_png}")
    print(f"Wrote {pal_path}")
