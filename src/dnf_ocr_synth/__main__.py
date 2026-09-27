"""Generate one PNG from the command line."""

import argparse
from pathlib import Path

from . import FontPaths, Renderer, estimate_ui_scale


def main() -> None:
    """Parse explicit font paths and save a self-describing PNG."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "text", help="Original CP949 nickname (up to 12 bytes)"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--profile", choices=("dotum", "nanum-neo"), default="dotum"
    )
    parser.add_argument(
        "--layout", choices=("metrics", "reference"), default="metrics"
    )
    parser.add_argument("--gulim", type=Path)
    parser.add_argument("--batang", type=Path)
    parser.add_argument("--nanum", type=Path)
    scaling = parser.add_mutually_exclusive_group()
    scaling.add_argument("--scale", type=float)
    scaling.add_argument("--ui-percent", type=float)
    parser.add_argument("--client-height", type=int, default=1080)
    args = parser.parse_args()
    try:
        scale = args.scale if args.scale is not None else 1.0
        if args.ui_percent is not None:
            scale = estimate_ui_scale(args.ui_percent, args.client_height)
        elif args.client_height != 1080:
            parser.error("--client-height requires --ui-percent")
        renderer = Renderer(FontPaths(args.gulim, args.batang, args.nanum))
        sample = renderer.render(
            args.text, profile=args.profile, layout=args.layout, scale=scale
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sample.save(args.output)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(args.output)


if __name__ == "__main__":
    main()
