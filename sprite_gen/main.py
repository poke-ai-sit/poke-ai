# sprite_gen/main.py
"""
CLI: python main.py <source_image> <pokemon_name> [--front-crop L U R D] [--back-crop L U R D]

Examples:
  python main.py assets/prata_generated.png charmander
  python main.py assets/prata_pro_generated.png charmeleon
  python main.py assets/frankson_generated.png squirtle
  python main.py assets/prata_generated.png charmander --front-crop 0 0 672 580 --back-crop 672 0 1344 580

Outputs go to: ../pokefirered/graphics/pokemon/<pokemon_name>/
  front.png, back.png, normal.pal
"""

import argparse
from pathlib import Path
from process import process_sprite


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert generated image to GBA sprite")
    parser.add_argument("source", type=Path, help="Path to the generated side-by-side image")
    parser.add_argument("pokemon_name", help="Folder name under pokefirered/graphics/pokemon/")
    parser.add_argument(
        "--front-crop", nargs=4, type=int, metavar=("L", "U", "R", "D"),
        help="Crop box for front sprite (left upper right lower pixels)",
    )
    parser.add_argument(
        "--back-crop", nargs=4, type=int, metavar=("L", "U", "R", "D"),
        help="Crop box for back sprite (left upper right lower pixels)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "pokefirered" / "graphics" / "pokemon" / args.pokemon_name

    if not out_dir.exists():
        print(f"ERROR: {out_dir} does not exist — check the pokemon_name argument")
        raise SystemExit(1)

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
