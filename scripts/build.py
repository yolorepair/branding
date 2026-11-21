#!/usr/bin/env python3
"""
YOLO Electronics Repair brand asset generator.

Reads brand.toml, produces:
  - logos/svg/*.svg     (mark, pulse, wordmark, lockup — all variants, vector)
  - logos/png/*.png     (all rasters at all configured sizes)
  - logos/favicon/*     (favicon.svg, favicon PNGs, favicon.ico, touch icon)
  - logos/favicon/site.webmanifest + maskable icons (PWA manifest)
  - logos/og/*.png      (Open Graph / social-share cards)
  - tokens/brand.css    (palette + fonts as :root CSS custom properties)
  - tokens/brand.json   (palette + fonts as structured JSON)

Usage:
    python scripts/build.py            # Build everything
    python scripts/build.py mark       # Build only the mark SVGs
    python scripts/build.py wordmark   # etc.
    python scripts/build.py --clean    # Remove generated files first

The configuration in brand.toml is the single source of truth for
colors, geometry, sizes, and variants. Edit there, not here.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
from functools import lru_cache
from pathlib import Path

import cairosvg
import tomllib  # Python 3.11+
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


# ─── Paths ──────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "brand.toml"
# Canonical artifacts live in logos/ — the directory downstream consumers fetch.
ASSETS_DIR = ROOT / "logos"
SVG_DIR = ASSETS_DIR / "svg"
PNG_DIR = ASSETS_DIR / "png"
FAVICON_DIR = ASSETS_DIR / "favicon"
OG_DIR = ASSETS_DIR / "og"
# Non-logo machine-readable exports (palette tokens) live one level up from
# logos/ so consumers can grab just the tokens without the whole asset tree.
TOKENS_DIR = ROOT / "tokens"
GENERATED_DIRS = (SVG_DIR, PNG_DIR, FAVICON_DIR, OG_DIR, TOKENS_DIR)

XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'


# ─── Config helpers ─────────────────────────────────────────────────

def load_config() -> dict:
    """Load brand.toml as a dict."""
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def color(cfg: dict, key: str) -> str:
    """Resolve a palette key (e.g. 'blue', 'ink') to its hex value."""
    for group in ("board", "neutrals"):
        if key in cfg["colors"][group]:
            return cfg["colors"][group][key]
    raise KeyError(f"Unknown color key: {key!r}")


def roles(cfg: dict, variant: str) -> dict:
    """Resolve a variant to {single, board, trace, text, label} hex colors."""
    var = cfg["variants"][variant]
    if var["mode"] == "single":
        c = color(cfg, var["single_color"])
        return {"single": True, "board": c, "trace": c, "text": c, "label": c}
    return {
        "single": False,
        "board": color(cfg, var["board"]),
        "trace": color(cfg, var["trace"]),
        "text": color(cfg, var["text"]),
        "label": color(cfg, var["label"]),
    }


def suffix(variant: str) -> str:
    """Filename suffix for a variant: color → '', mono_black → '-mono-black'."""
    return "" if variant == "color" else f"-{variant.replace('_', '-')}"


def n(x: float) -> str:
    """Format a number for SVG output: at most 3 decimals, no trailing zeros."""
    return f"{round(float(x), 3):g}"


def slug(cfg: dict) -> str:
    return cfg["meta"]["slug"]


def svg_doc(view_box: str, width: float, height: float, label: str,
            body: str, title: str | None = None, desc: str | None = None) -> str:
    """Wrap SVG body content in a standalone, accessible <svg> document."""
    head = f"  <title>{title or label}</title>"
    if desc:
        head += f"\n  <desc>{desc}</desc>"
    return (
        f'{XML_HEAD}<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'width="{n(width)}" height="{n(height)}" role="img" aria-label="{label}">\n'
        f"{head}\n{body}\n</svg>\n"
    )


# ─── Trace primitives ───────────────────────────────────────────────
#
# Everything in the brand is the same three things: a round-capped
# trace, a round pad with a drill hole, and a square pad.

def trace_path(d: str, width: float, stroke: str) -> str:
    return (
        f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{n(width)}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def dot(cx: float, cy: float, r: float, fill: str) -> str:
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"/>'


def ring(cx: float, cy: float, outer: float, inner: float, stroke: str) -> str:
    """A pad with a see-through drill hole — an annulus drawn as a stroke."""
    return (
        f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n((outer + inner) / 2)}" fill="none" '
        f'stroke="{stroke}" stroke-width="{n(outer - inner)}"/>'
    )


def square_pad(spec: list[float], fill: str) -> str:
    x, y, w, h, r = spec
    return (
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" '
        f'rx="{n(r)}" fill="{fill}"/>'
    )


def board(vb: float, shape: str, fill: str, extra: str = "") -> str:
    """The background behind a mark: a disc, or a full-bleed square tile."""
    if shape == "square":
        return f'<rect width="{n(vb)}" height="{n(vb)}" fill="{fill}"{extra}/>'
    return f'<circle cx="{n(vb / 2)}" cy="{n(vb / 2)}" r="{n(vb / 2)}" fill="{fill}"{extra}/>'


def circle_path(cx: float, cy: float, r: float) -> str:
    """A circle as path data, for use inside a compound clip path."""
    return (
        f"M{n(cx - r)} {n(cy)}a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0"
        f"a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0Z"
    )


def drilled(clip_id: str, vb: float, holes: list[tuple[float, float, float]], metal: str) -> str:
    """One-color copper with real holes: `metal` clipped to everything-but-`holes`.

    A clip path rather than a mask — masks are luminance in browsers and alpha
    in CairoSVG, so a mask can't render the same in both. Even-odd clipping does.
    """
    d = f"M{n(-vb)} {n(-vb)}H{n(2 * vb)}V{n(2 * vb)}H{n(-vb)}Z" + "".join(
        circle_path(x, y, r) for x, y, r in holes
    )
    return (
        f'<defs><clipPath id="{clip_id}"><path d="{d}" clip-rule="evenodd"/></clipPath></defs>'
        f'<g clip-path="url(#{clip_id})">{metal}</g>'
    )


# ─── The mark (Y-trace) ─────────────────────────────────────────────

def mark_body(cfg: dict, variant: str, shape: str = "disc") -> str:
    """SVG body for the Y-trace mark on its native grid."""
    m = cfg["mark"]
    vb = m["viewbox"]
    c = roles(cfg, variant)
    ax, ay = m["anchor"]
    xform = (
        f'transform="translate({n(ax)} {n(ay)}) scale({n(m["scale"])}) '
        f'translate({n(-vb / 2)} {n(-vb / 2)})"'
    )

    def layers(copper: str, drill: str) -> tuple[str, str]:
        metal = [trace_path(m["trace"], m["trace_width"], copper)]
        metal += [dot(x, y, m["pad_radius"], copper) for x, y in m["pads"]]
        holes = [dot(x, y, m["hole_radius"], drill) for x, y in m["pads"]]
        holes.append(dot(*m["via"], m["via_radius"], drill))
        return "".join(metal), "".join(holes)

    if c["single"]:
        # No board: the copper is the whole drawing, with the holes drilled through.
        metal, _ = layers(c["trace"], "none")
        drill = [(x, y, m["hole_radius"]) for x, y in m["pads"]]
        drill.append((*m["via"], m["via_radius"]))
        return f'  <g {xform}>{drilled(f"{slug(cfg)}-mark-drill", vb, drill, metal)}</g>'

    metal, holes = layers(c["trace"], c["board"])
    return (
        f'  {board(vb, shape, c["board"])}\n'
        f"  <g {xform}>\n    {metal}\n    {holes}\n  </g>"
    )


def mark_svg(cfg: dict, variant: str, shape: str = "disc") -> str:
    vb = cfg["mark"]["viewbox"]
    name = cfg["meta"]["name"]
    return svg_doc(f"0 0 {vb} {vb}", vb, vb, name, mark_body(cfg, variant, shape),
                   desc=cfg["mark"].get("description"))


def mark_variants(cfg: dict) -> list[str]:
    """The mark carries its own board, so it has no dark_bg form."""
    return [v for v in cfg["variants"] if v != "dark_bg"]


def write_marks(cfg: dict) -> list[Path]:
    written = []
    for variant in mark_variants(cfg):
        path = SVG_DIR / f"{slug(cfg)}-mark{suffix(variant)}.svg"
        path.write_text(mark_svg(cfg, variant))
        written.append(path)
    # The square tile: same mark, full-bleed, for anything a platform crops
    # itself (touch icons, maskable icons, social avatars).
    path = SVG_DIR / f"{slug(cfg)}-mark-square.svg"
    path.write_text(mark_svg(cfg, "color", "square"))
    written.append(path)
    return written


# ─── The pulse (secondary mark) ─────────────────────────────────────

def pulse_body(cfg: dict, variant: str) -> str:
    p = cfg["pulse"]
    vb = p["viewbox"]
    c = roles(cfg, variant)
    rx, ry = p["round_pad"]

    def layers(copper: str, drill: str) -> tuple[str, str]:
        metal = (
            square_pad(p["square_pad"], copper)
            + trace_path(p["trace"], p["trace_width"], copper)
            + dot(rx, ry, p["pad_radius"], copper)
        )
        return metal, dot(rx, ry, p["hole_radius"], drill)

    if c["single"]:
        # No board, and the trace stops short of the drill hole — a ring does it.
        return (
            f'  {square_pad(p["square_pad"], c["trace"])}'
            f'{trace_path(p["trace"], p["trace_width"], c["trace"])}'
            f'{ring(rx, ry, p["pad_radius"], p["hole_radius"], c["trace"])}'
        )

    metal, holes = layers(c["trace"], c["board"])
    return f'  {board(vb, "disc", c["board"])}\n  {metal}\n  {holes}'


def pulse_svg(cfg: dict, variant: str) -> str:
    vb = cfg["pulse"]["viewbox"]
    name = cfg["meta"]["name"]
    return svg_doc(f"0 0 {vb} {vb}", vb, vb, name, pulse_body(cfg, variant),
                   title=f"{name} — pulse", desc=cfg["pulse"].get("description"))


def write_pulses(cfg: dict) -> list[Path]:
    written = []
    for variant in mark_variants(cfg):
        path = SVG_DIR / f"{slug(cfg)}-pulse{suffix(variant)}.svg"
        path.write_text(pulse_svg(cfg, variant))
        written.append(path)
    return written


# ─── Type → outlines ────────────────────────────────────────────────

@lru_cache(maxsize=None)
def load_font(rel_path: str) -> TTFont:
    font_path = Path(rel_path)
    if not font_path.is_absolute():
        font_path = ROOT / font_path
    if not font_path.exists():
        raise FileNotFoundError(
            f"Font not found: {font_path}\n"
            f"The fonts are vendored in fonts/ — check the *font_path keys in brand.toml."
        )
    return TTFont(str(font_path))


def text_outlines(font_path: str, text: str, size: float, x: float, baseline: float,
                  letter_spacing: float = 0.0) -> tuple[str, float]:
    """
    Set `text` as glyph outlines starting at (x, baseline).

    Returns (svg_paths, advance) — the paths are unfilled, wrap them in a
    <g fill=…>. `advance` is the pen travel including trailing letter-spacing,
    the same way a browser measures a letterspaced run.
    """
    font = load_font(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    scale = size / font["head"].unitsPerEm

    paths = []
    pen_x = x
    for ch in text:
        glyph_name = cmap.get(ord(ch))
        if not glyph_name:
            raise ValueError(f"No glyph for character {ch!r} in {font_path}")
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        d = pen.getCommands()
        if d:
            paths.append(
                f'<path d="{d}" transform="translate({n(pen_x)} {n(baseline)}) '
                f'scale({n(scale)} {n(-scale)})"/>'
            )
        pen_x += hmtx[glyph_name][0] * scale + letter_spacing
    return "".join(paths), pen_x - x


# ─── Wordmark ───────────────────────────────────────────────────────

def wordmark_body(cfg: dict, variant: str) -> str:
    """SVG body for the wordmark, in the business card's pixel grid."""
    wm = cfg["wordmark"]
    name, desc, pulse = wm["name"], wm["descriptor"], wm["pulse"]
    c = roles(cfg, variant)

    letters = "".join(
        text_outlines(name["font_path"], ch, name["font_size"], x, name["baseline"])[0]
        for ch, x in name["letters"]
    )
    descriptor, _ = text_outlines(
        desc["font_path"], desc["text"], desc["font_size"],
        desc["x"], desc["baseline"], desc["letter_spacing"],
    )
    pads = "".join(
        ring(x, y, name["pad_radius"], name["hole_radius"], c["trace"])
        for x, y in name["pads"]
    )
    rule = (
        square_pad(pulse["square_pad"], c["trace"])
        + trace_path(pulse["trace"], pulse["trace_width"], c["trace"])
        + ring(*pulse["round_pad"], pulse["pad_radius"], pulse["hole_radius"], c["trace"])
    )
    return (
        f'  <g fill="{c["text"]}">{letters}</g>\n'
        f"  {pads}\n"
        f'  <g fill="{c["label"]}">{descriptor}</g>\n'
        f"  {rule}"
    )


def wordmark_svg(cfg: dict, variant: str) -> str:
    wm = cfg["wordmark"]
    x, y, w, h = wm["viewbox"]
    return svg_doc(f"{n(x)} {n(y)} {n(w)} {n(h)}", w, h, wm["aria_label"],
                   wordmark_body(cfg, variant))


def write_wordmarks(cfg: dict) -> list[Path]:
    written = []
    for variant in cfg["variants"]:
        path = SVG_DIR / f"{slug(cfg)}-wordmark{suffix(variant)}.svg"
        path.write_text(wordmark_svg(cfg, variant))
        written.append(path)
    return written


# ─── Lockup generation ──────────────────────────────────────────────

def lockup_svg(cfg: dict, variant: str) -> str:
    """Mark on the left, wordmark on the right, same height."""
    wx, wy, ww, wh = cfg["wordmark"]["viewbox"]
    gap = cfg["lockup"]["gap"]
    mark_vb = cfg["mark"]["viewbox"]
    mark_scale = wh / mark_vb
    total_w = wh + gap + ww

    # dark_bg has no mark of its own — the color mark is the one that goes on blue.
    mark_variant = "color" if variant == "dark_bg" else variant
    body = (
        f'  <g transform="scale({n(mark_scale)})">\n'
        f"  {mark_body(cfg, mark_variant)}\n"
        f"  </g>\n"
        f'  <g transform="translate({n(wh + gap - wx)} {n(-wy)})">\n'
        f"  {wordmark_body(cfg, variant)}\n"
        f"  </g>"
    )
    return svg_doc(f"0 0 {n(total_w)} {n(wh)}", total_w, wh, cfg["meta"]["name"], body)


def write_lockups(cfg: dict) -> list[Path]:
    written = []
    for variant in cfg["variants"]:
        path = SVG_DIR / f"{slug(cfg)}-lockup{suffix(variant)}.svg"
        path.write_text(lockup_svg(cfg, variant))
        written.append(path)
    return written


# ─── PNG rasterization ──────────────────────────────────────────────

def _png(svg: str, width: int, height: int | None = None) -> bytes:
    """Render an SVG string to PNG bytes (in memory)."""
    kwargs = {"output_width": width}
    if height is not None:
        kwargs["output_height"] = height
    return cairosvg.svg2png(bytestring=svg.encode(), **kwargs)


def rasterize_pngs(cfg: dict) -> list[Path]:
    """Render every SVG form at the configured sizes."""
    s = slug(cfg)
    jobs: list[tuple[str, str, int, bool]] = []  # (stem, svg, size, square)

    for variant in mark_variants(cfg):
        for size in cfg["sizes"]["mark"]["px"]:
            jobs.append((f"{s}-mark{suffix(variant)}", mark_svg(cfg, variant), size, True))
        for size in cfg["sizes"]["pulse"]["px"]:
            jobs.append((f"{s}-pulse{suffix(variant)}", pulse_svg(cfg, variant), size, True))
    for size in cfg["sizes"]["mark"]["px"]:
        jobs.append((f"{s}-mark-square", mark_svg(cfg, "color", "square"), size, True))

    for variant in cfg["variants"]:
        for size in cfg["sizes"]["lockup"]["px"]:
            jobs.append((f"{s}-lockup{suffix(variant)}", lockup_svg(cfg, variant), size, False))
        for size in cfg["sizes"]["wordmark"]["px"]:
            jobs.append((f"{s}-wordmark{suffix(variant)}", wordmark_svg(cfg, variant), size, False))

    written = []
    for stem, svg, size, square in jobs:
        dst = PNG_DIR / f"{stem}-{size}.png"
        dst.write_bytes(_png(svg, size, size if square else None))
        written.append(dst)
    return written


# ─── Favicons ───────────────────────────────────────────────────────

def _write_ico(pngs: dict[int, bytes], sizes: list[int], dst: Path) -> None:
    """Assemble a multi-resolution .ico with PNG-encoded entries — pure Python.

    Embeds the cairosvg PNGs verbatim, so the .ico is deterministic — unlike
    ImageMagick's encoder, whose output drifts between versions and would
    break the CI reproducibility gate.
    """
    header = struct.pack("<HHH", 0, 1, len(sizes))   # reserved, type=icon, count
    offset = 6 + 16 * len(sizes)
    entries, data = b"", b""
    for size in sizes:
        png = pngs[size]
        dim = size if size < 256 else 0              # 0 encodes 256 in the ICO dir
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        data += png
        offset += len(png)
    dst.write_bytes(header + entries + data)


def build_favicons(cfg: dict) -> list[Path]:
    """Generate the favicon set from the canonical color mark."""
    fav = cfg["sizes"]["favicon"]
    disc = mark_svg(cfg, "color")
    written = []

    svg_path = FAVICON_DIR / "favicon.svg"
    svg_path.write_text(disc)
    written.append(svg_path)

    pngs = {size: _png(disc, size, size) for size in set(fav["px"]) | set(fav["ico_sizes"])}
    for size in fav["px"]:
        dst = FAVICON_DIR / f"favicon-{size}.png"
        dst.write_bytes(pngs[size])
        written.append(dst)

    # Apple touch icon: iOS paints transparency black and rounds the corners
    # itself, so this one is the full-bleed square tile, not the disc.
    touch = fav["touch_px"]
    dst = FAVICON_DIR / f"favicon-{touch}.png"
    dst.write_bytes(_png(mark_svg(cfg, "color", "square"), touch, touch))
    written.append(dst)

    ico_path = FAVICON_DIR / "favicon.ico"
    _write_ico(pngs, fav["ico_sizes"], ico_path)
    written.append(ico_path)
    return written


# ─── Web app manifest + maskable icons ──────────────────────────────

def build_manifest(cfg: dict) -> list[Path]:
    """Emit site.webmanifest + maskable icons (the square tile)."""
    mf = cfg["manifest"]
    tile = mark_svg(cfg, "color", "square")
    written = []

    for size in mf["maskable_sizes"]:
        dst = FAVICON_DIR / f"favicon-maskable-{size}.png"
        dst.write_bytes(_png(tile, size, size))
        written.append(dst)

    # Manifest. src paths are bare filenames — the manifest sits beside the
    # icons in logos/favicon/; consumers adjust src to their served path.
    manifest = {
        "name": mf["name"],
        "short_name": mf["short_name"],
        "theme_color": color(cfg, mf["theme_color"]),
        "background_color": color(cfg, mf["background_color"]),
        "display": mf["display"],
        "icons": [
            {"src": "favicon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "favicon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            *[
                {"src": f"favicon-maskable-{s}.png", "sizes": f"{s}x{s}",
                 "type": "image/png", "purpose": "maskable"}
                for s in mf["maskable_sizes"]
            ],
        ],
    }
    dst = FAVICON_DIR / "site.webmanifest"
    dst.write_text(json.dumps(manifest, indent=2) + "\n")
    written.append(dst)
    return written


# ─── Open Graph / social cards ──────────────────────────────────────

def build_og(cfg: dict) -> list[Path]:
    """Render social-share cards: wordmark + tagline centered on solder-mask blue."""
    og = cfg["og"]
    bg = color(cfg, og["background"])
    wx, wy, ww, wh = cfg["wordmark"]["viewbox"]
    wm_body = wordmark_body(cfg, og["wordmark_variant"])
    tagline = cfg["meta"]["tagline"]
    font = load_font(og["tagline_font_path"])
    cap_ratio = font["OS/2"].sCapHeight / font["head"].unitsPerEm

    written = []
    for W, H in og["sizes"].values():
        wm_scale = W * og["wordmark_width"] / ww
        wm_h = wh * wm_scale
        tag_size = H * og["tagline_size"]
        tag_cap = tag_size * cap_ratio
        gap = H * og["tagline_gap"]

        top = (H - (wm_h + gap + tag_cap)) / 2
        wm_x = (W - ww * wm_scale) / 2
        _, tag_w = text_outlines(og["tagline_font_path"], tagline, tag_size, 0, 0)
        tag_paths, _ = text_outlines(
            og["tagline_font_path"], tagline, tag_size,
            (W - tag_w) / 2, top + wm_h + gap + tag_cap,
        )

        svg = (
            f'{XML_HEAD}<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
            f'  <rect width="{W}" height="{H}" fill="{bg}"/>\n'
            f'  <g transform="translate({n(wm_x)} {n(top)}) scale({n(wm_scale)}) '
            f'translate({n(-wx)} {n(-wy)})">\n'
            f"  {wm_body}\n"
            f"  </g>\n"
            f'  <g fill="{color(cfg, og["tagline_color"])}">{tag_paths}</g>\n'
            f"</svg>\n"
        )
        dst = OG_DIR / f"{slug(cfg)}-og-{W}x{H}.png"
        dst.write_bytes(_png(svg, W, H))
        written.append(dst)
    return written


# ─── Token export (CSS + JSON) ──────────────────────────────────────

def _css_var(prefix: str, key: str) -> str:
    """Map a palette key to a CSS custom-property name: primary_accent → --yolo-primary-accent."""
    return f"--{prefix}-{key.replace('_', '-')}"


def _font_stack(spec: dict) -> str:
    return f"'{spec['family']}', {spec['fallback']}"


def write_tokens(cfg: dict) -> list[Path]:
    """Export the palette + fonts as tokens/brand.css (:root vars) + tokens/brand.json.

    Sourced straight from [colors.*] and [fonts.*] so consumers reference the
    brand instead of hand-copying hexes. tomllib preserves insertion order, so
    output is deterministic.
    """
    prefix = cfg["tokens"]["css_prefix"]
    name = cfg["meta"]["name"]
    board_colors = cfg["colors"]["board"]
    neutrals = cfg["colors"]["neutrals"]
    semantics = cfg["colors"]["semantics"]
    fonts = cfg["fonts"]

    # CSS
    lines = [
        f"/* {name} brand tokens — generated from brand.toml by scripts/build.py.",
        " * Do not edit by hand; run `make tokens`. */",
        ":root {",
        "  /* The board — solder mask and copper. */",
    ]
    lines += [f"  {_css_var(prefix, k)}: {v};" for k, v in board_colors.items()]
    lines.append("  /* Neutrals. */")
    lines += [f"  {_css_var(prefix, k)}: {v};" for k, v in neutrals.items()]
    lines.append("  /* Semantic aliases. */")
    lines += [
        f"  {_css_var(prefix, k)}: var({_css_var(prefix, target)});"
        for k, target in semantics.items()
    ]
    lines.append("  /* Font stacks. */")
    lines += [
        f"  {_css_var(prefix, f'font_{role}')}: {_font_stack(spec)};"
        for role, spec in fonts.items()
    ]
    lines.append("}")
    css = "\n".join(lines) + "\n"

    # JSON
    data = {
        "meta": {k: cfg["meta"][k] for k in ("name", "short_name", "slug", "tagline")},
        "board": dict(board_colors),
        "neutrals": dict(neutrals),
        "semantics": {k: color(cfg, t) for k, t in semantics.items()},
        "fonts": {
            role: {"family": spec["family"], "weights": spec["weights"],
                   "stack": _font_stack(spec)}
            for role, spec in fonts.items()
        },
    }
    js = json.dumps(data, indent=2) + "\n"

    css_path = TOKENS_DIR / "brand.css"
    json_path = TOKENS_DIR / "brand.json"
    css_path.write_text(css)
    json_path.write_text(js)
    return [css_path, json_path]


# ─── Cleanup and CLI ────────────────────────────────────────────────

def clean():
    """Remove all generated assets."""
    for d in GENERATED_DIRS:
        if d.exists():
            shutil.rmtree(d)
            print(f"  removed {d.relative_to(ROOT)}")
    ensure_dirs()


def ensure_dirs():
    for d in GENERATED_DIRS:
        d.mkdir(parents=True, exist_ok=True)


TARGETS = ["mark", "pulse", "wordmark", "lockup", "png", "favicon", "manifest", "og", "tokens"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    parser.add_argument(
        "targets", nargs="*", choices=["all", *TARGETS, []], default=[],
        help="Which assets to build (default: all)",
    )
    parser.add_argument("--clean", action="store_true", help="Remove generated files first")
    args = parser.parse_args()

    cfg = load_config()
    ensure_dirs()

    if args.clean:
        print("Cleaning…")
        clean()

    targets = set(args.targets) if args.targets else {"all"}
    if "all" in targets:
        targets = set(TARGETS)

    def report(paths: list[Path]) -> None:
        for p in paths:
            print(f"  {p.relative_to(ROOT)}")

    if "mark" in targets:
        print("Building mark SVGs…")
        report(write_marks(cfg))
    if "pulse" in targets:
        print("Building pulse SVGs…")
        report(write_pulses(cfg))
    if "wordmark" in targets:
        print("Building wordmark SVGs…")
        report(write_wordmarks(cfg))
    if "lockup" in targets:
        print("Building lockup SVGs…")
        report(write_lockups(cfg))
    if "png" in targets:
        print("Rasterizing PNGs…")
        pngs = rasterize_pngs(cfg)
        print(f"  {len(pngs)} PNG files written to {PNG_DIR.relative_to(ROOT)}/")
    if "favicon" in targets:
        print("Building favicons…")
        report(build_favicons(cfg))
    if "manifest" in targets:
        print("Building web manifest + maskable icons…")
        report(build_manifest(cfg))
    if "og" in targets:
        print("Building OG social cards…")
        report(build_og(cfg))
    if "tokens" in targets:
        print("Exporting brand tokens…")
        report(write_tokens(cfg))

    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
