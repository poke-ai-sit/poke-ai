# sprite_gen/process.py
"""
Convert generated images into GBA-ready sprites and icons for pokefirered.

process_sprite: side-by-side image → two 64x64 indexed PNGs + JASC-PAL
process_icon:   single icon image → 32x64 indexed PNG + JASC-PAL (two 32x32 frames stacked)

Transparency convention: palette index 0 is the GBA transparent color.
We use magenta (#FF00FF) as the fill sentinel for transparent areas — it never appears
in real artwork, so car windows/highlights (which are white) stay at non-zero indices
and render correctly instead of becoming transparent holes.
"""

from pathlib import Path
from PIL import Image

# Sentinel color for transparency. Must not appear anywhere in real sprite artwork.
_TRANSPARENT_SENTINEL = (255, 0, 255)  # magenta


def _build_unified_palette(regions: list[Image.Image]) -> list[int]:
    """
    Quantize all regions together to produce a shared 16-color palette.
    Returns a flat palette list [R0,G0,B0, R1,G1,B1, ...] with 16 entries,
    magenta guaranteed at index 0 (GBA transparent slot).
    """
    total_w = sum(r.width for r in regions)
    max_h = max(r.height for r in regions)
    combined = Image.new("RGB", (total_w, max_h), _TRANSPARENT_SENTINEL)
    x = 0
    for r in regions:
        combined.paste(r, (x, 0))
        x += r.width

    quantized = combined.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:16 * 3]

    # Swap magenta to index 0 — GBA treats index 0 as transparent for sprites/icons
    magenta_idx = None
    for i in range(16):
        r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        if r >= 240 and g <= 15 and b >= 240:
            magenta_idx = i
            break

    if magenta_idx is not None and magenta_idx != 0:
        for ch in range(3):
            palette[ch], palette[magenta_idx * 3 + ch] = (
                palette[magenta_idx * 3 + ch],
                palette[ch],
            )

    return palette


def _apply_palette(region: Image.Image, palette: list[int]) -> Image.Image:
    """Re-quantize a region using a fixed 16-color palette, indices clamped to 0-15."""
    import numpy as np
    pal_img = Image.new("P", (1, 1))
    # Repeat the 16 colors to fill all 256 slots so PIL never maps a pixel to index >15.
    full_palette = (palette * 16)[:768]
    pal_img.putpalette(full_palette)
    quantized = region.quantize(palette=pal_img, dither=0)
    # Safety clamp: ensure no index exceeds 15
    arr = np.array(quantized)
    arr = np.clip(arr, 0, 15).astype(np.uint8)
    result = Image.fromarray(arr, mode="P")
    result.putpalette(palette + [0] * (768 - len(palette)))
    return result


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
    """Paste RGBA image onto a magenta background (transparency sentinel)."""
    bg = Image.new("RGB", img.size, _TRANSPARENT_SENTINEL)
    if img.mode == "RGBA":
        bg.paste(img, mask=img.split()[3])
    else:
        bg.paste(img)
    return bg


def _snap_sentinel(img: Image.Image) -> Image.Image:
    """
    After LANCZOS resize, edge pixels blend the sentinel with real colors,
    creating dozens of near-magenta variants that waste palette slots.
    Snap any pixel with low green channel (G < 32) and high R+B to exact magenta.
    """
    import numpy as np
    arr = np.array(img, dtype=np.int32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Near-sentinel: high red, low green, high blue
    mask = (r > 180) & (g < 32) & (b > 180)
    arr[mask] = [255, 0, 255]
    return Image.fromarray(arr.astype(np.uint8), "RGB")


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

    front_rgb = _snap_sentinel(_flatten_alpha(img.crop(front_crop)).resize((64, 64), Image.LANCZOS))
    back_rgb = _snap_sentinel(_flatten_alpha(img.crop(back_crop)).resize((64, 64), Image.LANCZOS))

    palette = _build_unified_palette([front_rgb, back_rgb])

    front_indexed = _apply_palette(front_rgb, palette)
    back_indexed = _apply_palette(back_rgb, palette)

    front_indexed.save(front_png)
    back_indexed.save(back_png)
    write_jasc_pal(palette, pal_path)

    print(f"Wrote {front_png}")
    print(f"Wrote {back_png}")
    print(f"Wrote {pal_path}")


def process_icon(
    source_path: Path,
    icon_png: Path,
    pal_path: Path | None = None,
) -> None:
    """
    Convert a single icon image to GBA format.

    Writes:
      icon_png  — 32x64 indexed PNG (two identical 32x32 frames stacked)
      pal_path  — JASC-PAL for this icon (optional; needed to update icon_palettes/)

    Palette index 0 = magenta sentinel = GBA transparent.
    """
    img = Image.open(source_path).convert("RGBA")
    frame_rgb = _snap_sentinel(_flatten_alpha(img).resize((32, 32), Image.LANCZOS))

    palette = _build_unified_palette([frame_rgb])
    frame_indexed = _apply_palette(frame_rgb, palette)

    icon = Image.new("P", (32, 64))
    icon.putpalette(palette + [0] * (768 - len(palette)))
    icon.paste(frame_indexed, (0, 0))
    icon.paste(frame_indexed, (0, 32))
    icon.save(icon_png)

    colors_used = len(set(frame_indexed.getdata()))
    print(f"Wrote {icon_png}  [32x64, {colors_used} colors]")

    if pal_path is not None:
        write_jasc_pal(palette, pal_path)
        print(f"Wrote {pal_path}")
