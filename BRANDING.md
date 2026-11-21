# YOLO Electronics Repair Brand Guidelines

Logo, colors, typography, and usage rules for YOLO Electronics Repair —
board-level electronics repair in West Sacramento, CA.

This document is authoritative. If something's going on the site, a
card, a sticker, a shirt, or a shipping label, these are the rules.
They exist so the shop looks like one shop everywhere it shows up.

> **This file is partly generated.** The tables below live in
> `<!-- GENERATED -->` blocks that `scripts/render_branding_md.py`
> rebuilds from `brand.toml`. Everything else is hand-written prose,
> preserved verbatim across rebuilds — edit it freely. Run `make check`
> to verify the generated tables are in sync with `brand.toml`.

---

## The idea

The brand is a circuit board. Solder-mask blue is the board, copper is
anything that conducts, and off-white is the silkscreen printed on top.
Every shape in the kit is one of three things a board is actually made
of: a **trace**, a **round pad** with a drill hole, or a **square pad**.

**If it wouldn't pass for something on a PCB, it's not on brand.**

Name: **YOLO Electronics Repair**. Handle: `@yolo.repair`. Tagline:

> You let the smoke out. We put it back in.

---

## The mark

The mark is the **Y-trace** — a PCB trace in the shape of a Y. Three
pads, two 45° doglegs, and a via where the branches meet, on a
solder-mask blue disc.

The trace is drawn smaller than the disc on purpose. Every platform
that shows an avatar crops it to a circle or a squircle, and the
padding means nothing gets clipped when they do.

Two shapes of the same drawing:

- `yolo-mark` — the disc. Transparent corners. Use it anywhere you
  control the shape.
- `yolo-mark-square` — the same trace on a full-bleed blue square. Use
  it anywhere the platform does its own cropping: touch icons, app
  icons, social avatars.

### The pulse

The **pulse** is the secondary mark: a trace with a heartbeat in it,
square pad in, round pad out. It's the "we put it back in" half of the
tagline. It shows up two ways — as a roundel (`yolo-pulse`) and as the
long rule under the wordmark.

The Y-trace is the logo. The pulse is a supporting device — use it as a
divider, a card back, a sticker. Don't use it as the avatar.

### The wordmark

`YOLO` in Barlow Condensed ExtraBold with both O's swapped for copper
pads, `ELECTRONICS REPAIR` letterspaced in IBM Plex Mono underneath, and
the pulse as a rule below that. This is the business card front,
measured off the card and redrawn — same proportions, to the pixel.

The **lockup** is the mark and the wordmark side by side.

---

## Variants

Four color treatments are provided. Use the most expressive one your
context supports.

<!-- GENERATED:variants-table -->
| Variant | Use when |
|---------|----------|
| **Color** (canonical) | Light backgrounds — paper, white web pages, invoices, the business cards. The default |
| **Color, dark-bg** | Blue or dark backgrounds — the site, social headers, anything printed on solder-mask blue. The lettering flips to silkscreen off-white |
| **Mono black** | One-color black — rubber stamps, thermal receipt printers, laser engraving, fax-grade photocopies |
| **Mono white** | One-color white — vinyl on a dark toolbox, etched glass, a reversed stamp on a dark bag |
<!-- /GENERATED -->

The mark and the pulse carry their own blue disc, so they have no
dark-bg form — the color version is already the dark-bg version. In the
mono variants the disc drops away entirely: what's left is the copper
layer on its own, holes drilled clean through.

---

## Color palette

<!-- GENERATED:palette-table -->
| Color | Hex | Token | Use |
|-------|-----|-------|-----|
| **Solder-mask blue** | `#1E4D9B` | `--yolo-blue` | the board. Backgrounds, the disc behind the mark, lettering on paper |
| **Deep blue** | `#163D7E` | `--yolo-deep` | the darker board. Page backgrounds, footers, pressed and hover states |
| **Copper** | `#E0A050` | `--yolo-copper` | anything that conducts. Traces, pads, the O's, labels on blue |
| **Ink** | `#F3F2EE` | `--yolo-ink` | silkscreen. Primary text on blue |
| **Soft** | `#D6DCEA` | `--yolo-soft` | secondary text on blue — captions, metadata |
| **Black** | `#000000` | `--yolo-black` | one-color print only |
| **White** | `#FFFFFF` | `--yolo-white` | one-color print only, and paper |
<!-- /GENERATED -->

When only one color is allowed, it's **solder-mask blue**.

**Ink is the light one.** The name comes from silkscreen ink, which is
white on a board — it's the text color *on blue*, not a dark text color
for paper. On paper, lettering is solder-mask blue.

Copper is an accent, not a text color on white. `#E0A050` on white is
about 2.2:1 — fine for a trace or a pad, unreadable as body copy. On
blue it's about 3.6:1, which is enough for large type and short labels
(`ELECTRONICS REPAIR`) and not enough for a paragraph.

Don't hand-copy the hexes. `tokens/brand.css` and `tokens/brand.json`
are generated from the same table.

---

## Typography

<!-- GENERATED:fonts-table -->
| Role | Font | Weights | Token |
|------|------|---------|-------|
| Display — headlines, the tagline, anything loud | Barlow Condensed | 600 / 800 | `--yolo-font-display` |
| Mono — labels, contact details, part numbers, body copy | IBM Plex Mono | 400 / 600 | `--yolo-font-mono` |
<!-- /GENERATED -->

Both are free, open-licensed (OFL), and on Google Fonts.

The wordmark is provided as **vector paths embedded in the SVG**, so no
font installation is required anywhere the SVG renders. Don't re-set it
in live type — the O's aren't letters, they're pads, and a font can't
give you that.

Mono labels are set in caps with wide tracking (`0.2em`), the way a
board labels its connectors: `J1`, `J2`, `LAPTOPS · GPUS · DJ GEAR ·
RETRO`.

---

## Usage rules

### Do

- Use the color mark whenever the context renders color.
- Use the lockup on first appearance; after that the mark alone is fine.
- Keep clear space around the mark of at least **one pad** — the
  diameter of one of the three round pads.
- Use the dark-bg wordmark on blue so the `Y` and `L` have contrast.
- Use the square tile, not the disc, wherever the platform crops for you.

### Don't

- Don't recolor the mark outside the provided variants.
- Don't rotate, skew, or stretch it.
- Don't redraw the trace. Four slightly different Y-traces existed
  before this repo did; that's the problem it's here to end.
- Don't fill in the drill holes or drop the via.
- Don't add shadows, glows, gradients, or bevels.
- Don't put the color mark on a mid-blue background that isn't
  solder-mask blue — the disc edge goes muddy. Use `#1E4D9B` exactly,
  or something clearly lighter or darker.
- Don't set the tagline in the mono font. It's a headline; it gets
  Barlow Condensed.

### Minimum sizes

| Asset | Minimum render size |
|-------|---------------------|
| Mark (color or mono) | 16×16 px — the via closes up below that |
| Pulse roundel | 24×24 px |
| Wordmark | 120 px wide — `ELECTRONICS REPAIR` stops being legible below that |
| Lockup | 180 px wide |

For favicons, use the multi-resolution `favicon.ico` or `favicon.svg`.

---

## Files in this kit

```
logos/
├── svg/
│   ├── yolo-mark.svg                 ← canonical mark, on its disc
│   ├── yolo-mark-square.svg          ← same mark, full-bleed square tile
│   ├── yolo-mark-mono-black.svg      ← copper layer only, one color
│   ├── yolo-mark-mono-white.svg
│   ├── yolo-pulse.svg                ← secondary mark, on its disc
│   ├── yolo-pulse-mono-black.svg
│   ├── yolo-pulse-mono-white.svg
│   ├── yolo-wordmark.svg             ← wordmark for light bg
│   ├── yolo-wordmark-dark-bg.svg     ← wordmark for blue / dark bg
│   ├── yolo-wordmark-mono-black.svg
│   ├── yolo-wordmark-mono-white.svg
│   ├── yolo-lockup.svg               ← mark + wordmark, light bg
│   ├── yolo-lockup-dark-bg.svg       ← mark + wordmark, blue / dark bg
│   ├── yolo-lockup-mono-black.svg
│   └── yolo-lockup-mono-white.svg
├── png/
│   ├── yolo-mark-{32,64,128,256,460,512,1024}.png
│   ├── yolo-mark-square-{...}.png
│   ├── yolo-mark-mono-black-{...}.png
│   ├── yolo-mark-mono-white-{...}.png
│   ├── yolo-pulse-{64,256,512,1024}.png
│   ├── yolo-pulse-mono-black-{...}.png
│   ├── yolo-pulse-mono-white-{...}.png
│   ├── yolo-wordmark-{200,400,800,1600}.png
│   ├── yolo-wordmark-dark-bg-{...}.png
│   ├── yolo-wordmark-mono-black-{...}.png
│   ├── yolo-wordmark-mono-white-{...}.png
│   ├── yolo-lockup-{400,800,1200,2400}.png
│   ├── yolo-lockup-dark-bg-{...}.png
│   ├── yolo-lockup-mono-black-{...}.png
│   └── yolo-lockup-mono-white-{...}.png
├── favicon/
│   ├── favicon.svg             ← the mark, for browsers that take SVG
│   ├── favicon.ico             ← multi-resolution legacy favicon
│   ├── favicon-{16,32,48,64,192,512}.png
│   ├── favicon-180.png         ← Apple touch icon (square tile)
│   ├── favicon-maskable-{192,512}.png
│   └── site.webmanifest
└── og/
    ├── yolo-og-1200x630.png    ← og:image
    └── yolo-og-1280x640.png    ← GitHub social preview
tokens/
├── brand.css                   ← palette + font stacks as :root custom properties
└── brand.json                  ← same, structured
```

---

## Avatars

Upload the **square tile**, not the disc — the platform crops it round
for you, and a disc inside a circle crop leaves a hairline of whatever's
behind it.

| Where | File |
|-------|------|
| GitHub org avatar | `logos/png/yolo-mark-square-460.png` |
| Instagram, Facebook, Google Business | `logos/png/yolo-mark-square-1024.png` |

---

## Credits

- **Type**: Barlow Condensed by Jeremy Tribby, IBM Plex Mono by IBM —
  both SIL Open Font License. Licenses are in `fonts/`.
- **First version**: 2026, by Aaron Cupp + Claude.
