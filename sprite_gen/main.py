# sprite_gen/main.py
"""
CLI: python main.py <source_image> <pokemon_name> [options]

Sprite (front + back):
  python main.py assets/prata_generated.png charmander
  python main.py assets/prata_pro_generated.png charmeleon
  python main.py assets/frankson_generated.png squirtle
  python main.py assets/prata_generated.png charmander --front-crop 0 0 672 580 --back-crop 672 0 1344 580

Icon (Pokédex icon, 32x64 two-frame):
  python main.py assets/prata_icon.png charmander --icon --icon-pal-slot 0
  python main.py assets/prata_pro_icon.png charmeleon --icon --icon-pal-slot 1
  python main.py assets/frankson_icon.png squirtle --icon --icon-pal-slot 2

Outputs go to: ../pokefirered/graphics/pokemon/<pokemon_name>/
  front.png, back.png, normal.pal  (sprite mode)
  icon.png                          (icon mode)
  ../pokefirered/graphics/pokemon/icon_palettes/icon_palette_N.pal  (if --icon-pal-slot given)
"""

import argparse
from pathlib import Path
from process import process_sprite, process_icon


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert generated image to GBA sprite or icon")
    parser.add_argument("source", type=Path, help="Path to the source image")
    parser.add_argument("pokemon_name", help="Folder name under pokefirered/graphics/pokemon/")
    parser.add_argument(
        "--icon", action="store_true",
        help="Generate icon.png (32x64, 4bpp) instead of front/back sprites",
    )
    parser.add_argument(
        "--icon-pal-slot", type=int, metavar="N",
        help="Also write the icon palette to icon_palettes/icon_palette_N.pal (0, 1, or 2)",
    )
    parser.add_argument(
        "--front-crop", nargs=4, type=int, metavar=("L", "U", "R", "D"),
        help="Crop box for front sprite (sprite mode only)",
    )
    parser.add_argument(
        "--back-crop", nargs=4, type=int, metavar=("L", "U", "R", "D"),
        help="Crop box for back sprite (sprite mode only)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "pokefirered" / "graphics" / "pokemon" / args.pokemon_name

    if not out_dir.exists():
        print(f"ERROR: {out_dir} does not exist — check the pokemon_name argument")
        raise SystemExit(1)

    if args.icon:
        pal_path = None
        if args.icon_pal_slot is not None:
            pal_dir = repo_root / "pokefirered" / "graphics" / "pokemon" / "icon_palettes"
            pal_path = pal_dir / f"icon_palette_{args.icon_pal_slot}.pal"
        process_icon(
            source_path=args.source,
            icon_png=out_dir / "icon.png",
            pal_path=pal_path,
        )
    else:
        front_crop = tuple(args.front_crop) if args.front_crop else None
        back_crop = tuple(args.back_crop) if args.back_crop else None
        process_sprite(
            source_path=args.source,
            front_png=out_dir / "front.png",
            back_png=out_dir / "back.png",
            pal_path=out_dir / "normal.pal",
            front_crop=front_crop,
            back_crop=back_crop,
        )


if __name__ == "__main__":
    main()
