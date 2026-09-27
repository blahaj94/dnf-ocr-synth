"""Generate one PNG from the command line."""

import sys

from . import FontPaths, Renderer
from .cli import parse_args


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
            color=args.color,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sample.save(args.output)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    print(args.output)


if __name__ == "__main__":
    main()
