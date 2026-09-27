"""Generate one PNG from the command line."""

import argparse
import sys
from pathlib import Path

from . import FontPaths, Renderer, estimate_ui_scale


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI options and resolve the requested image scale."""
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
    args = parser.parse_args(argv)
    if args.ui_percent is not None:
        try:
            args.scale = estimate_ui_scale(args.ui_percent, args.client_height)
        except ValueError as error:
            parser.exit(2, f"error: {error}\n")
    elif args.client_height != 1080:
        parser.error("--client-height requires --ui-percent")
    elif args.scale is None:
        args.scale = 1.0
    return args


def main() -> None:
    """Render and save a PNG using the parsed CLI options."""
    args = parse_args()
    try:
        renderer = Renderer(FontPaths(args.gulim, args.batang, args.nanum))
        sample = renderer.render(
            args.text,
            profile=args.profile,
            layout=args.layout,
            scale=args.scale,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sample.save(args.output)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    print(args.output)


if __name__ == "__main__":
    main()
