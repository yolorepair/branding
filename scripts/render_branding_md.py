#!/usr/bin/env python3
"""
Keep the generated tables in BRANDING.md in sync with brand.toml.

BRANDING.md is the source of truth for its own prose. A few regions are
*facts* that must match brand.toml exactly — the palette table, the
variants table, and the fonts table. Those regions are wrapped in markers:

    <!-- GENERATED:palette-table -->
    ...table body, rewritten from brand.toml...
    <!-- /GENERATED -->

Everything outside a GENERATED block is hand-written prose and is
preserved verbatim.

Usage:
    python scripts/render_branding_md.py            # Rewrite GENERATED blocks in place
    python scripts/render_branding_md.py --check    # Exit 1 if any block is stale (CI)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "brand.toml"
OUTPUT_PATH = ROOT / "BRANDING.md"

COLOR_FRIENDLY = {
    "blue": "Solder-mask blue",
    "deep": "Deep blue",
    "copper": "Copper",
    "ink": "Ink",
    "soft": "Soft",
    "black": "Black",
    "white": "White",
}
COLOR_DESCRIPTION = {
    "blue": "the board. Backgrounds, the disc behind the mark, lettering on paper",
    "deep": "the darker board. Page backgrounds, footers, pressed and hover states",
    "copper": "anything that conducts. Traces, pads, the O's, labels on blue",
    "ink": "silkscreen. Primary text on blue",
    "soft": "secondary text on blue — captions, metadata",
    "black": "one-color print only",
    "white": "one-color print only, and paper",
}
VARIANT_FRIENDLY = {
    "color": "**Color** (canonical)",
    "dark_bg": "**Color, dark-bg**",
    "mono_black": "**Mono black**",
    "mono_white": "**Mono white**",
}
FONT_ROLE = {
    "display": "Display — headlines, the tagline, anything loud",
    "mono": "Mono — labels, contact details, part numbers, body copy",
}


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


# ─── Generated-block renderers ──────────────────────────────────────

def render_palette_table(cfg: dict) -> str:
    prefix = cfg["tokens"]["css_prefix"]
    lines = ["| Color | Hex | Token | Use |", "|-------|-----|-------|-----|"]
    for group in ("board", "neutrals"):
        for key, hex_val in cfg["colors"][group].items():
            lines.append(
                f"| **{COLOR_FRIENDLY.get(key, key)}** | `{hex_val}` | "
                f"`--{prefix}-{key.replace('_', '-')}` | {COLOR_DESCRIPTION.get(key, key)} |"
            )
    return "\n".join(lines)


def render_variants_table(cfg: dict) -> str:
    lines = ["| Variant | Use when |", "|---------|----------|"]
    for variant_name, var in cfg["variants"].items():
        if not var.get("show_in_table", True):
            continue
        friendly = VARIANT_FRIENDLY.get(variant_name, variant_name)
        lines.append(f"| {friendly} | {var['purpose']} |")
    return "\n".join(lines)


def render_fonts_table(cfg: dict) -> str:
    prefix = cfg["tokens"]["css_prefix"]
    lines = ["| Role | Font | Weights | Token |", "|------|------|---------|-------|"]
    for role, spec in cfg["fonts"].items():
        weights = " / ".join(str(w) for w in spec["weights"])
        lines.append(
            f"| {FONT_ROLE.get(role, role)} | {spec['family']} | {weights} | "
            f"`--{prefix}-font-{role}` |"
        )
    return "\n".join(lines)


GENERATORS = {
    "palette-table": render_palette_table,
    "variants-table": render_variants_table,
    "fonts-table": render_fonts_table,
}

BLOCK_RE = re.compile(
    r"(?P<open><!-- GENERATED:(?P<name>[\w-]+) -->\n)"
    r"(?P<body>.*?)"
    r"(?P<close>\n<!-- /GENERATED -->)",
    re.DOTALL,
)


def rewrite_blocks(cfg: dict, text: str) -> str:
    """Replace the body of every GENERATED block with freshly-rendered content."""
    seen: set[str] = set()

    def repl(m: re.Match) -> str:
        name = m.group("name")
        seen.add(name)
        gen = GENERATORS.get(name)
        if gen is None:
            raise ValueError(
                f"Unknown GENERATED block {name!r} in BRANDING.md. "
                f"Known blocks: {', '.join(sorted(GENERATORS))}."
            )
        return f"{m.group('open')}{gen(cfg)}{m.group('close')}"

    result = BLOCK_RE.sub(repl, text)
    missing = set(GENERATORS) - seen
    if missing:
        raise ValueError(
            f"BRANDING.md is missing GENERATED blocks: {', '.join(sorted(missing))}."
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync BRANDING.md generated blocks with brand.toml")
    parser.add_argument("--check", action="store_true",
                        help="Exit 1 if any generated block is out of sync (for CI)")
    args = parser.parse_args()

    cfg = load_config()
    if not OUTPUT_PATH.exists():
        print("BRANDING.md missing", file=sys.stderr)
        sys.exit(1)
    current = OUTPUT_PATH.read_text()
    updated = rewrite_blocks(cfg, current)

    if args.check:
        if current != updated:
            print(
                "BRANDING.md generated blocks are out of sync with brand.toml.\n"
                "Run: python scripts/render_branding_md.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print("BRANDING.md is in sync.")
        return

    OUTPUT_PATH.write_text(updated)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
