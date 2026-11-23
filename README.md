# YOLO Electronics Repair Brand Assets

The logo files and brand guidelines for YOLO Electronics Repair —
board-level repair in West Sacramento, CA. See `BRANDING.md` for usage
rules, color values, and typography.

This repo exists because the logo used to live in five places and none
of them agreed. Now there's one drawing, and everything else is
generated from it.

## Quick start

- **Website favicon:** `logos/favicon/favicon.svg`, with
  `logos/favicon/favicon.ico` as the fallback
- **Apple touch icon:** `logos/favicon/favicon-180.png`
- **Link preview (`og:image`):** `logos/og/yolo-og-1200x630.png`
- **Social / GitHub avatar:** `logos/png/yolo-mark-square-1024.png`
  (or `-460` for GitHub)
- **Page header on blue:** `logos/svg/yolo-lockup-dark-bg.svg`
- **Invoice, letterhead, anything on paper:** `logos/svg/yolo-lockup.svg`
- **Rubber stamp, receipt printer, engraving:** the `-mono-black` files
- **Colors and fonts in CSS:** `tokens/brand.css`

## Browse the assets

Open `preview.html` in a browser to see every variant rendered at
working sizes against light and dark backgrounds.

## Files

```
.
├── BRANDING.md         ← usage rules, colors, fonts, do's and don'ts
├── README.md           ← this file
├── preview.html        ← visual inventory of every asset
├── brand.toml          ← the source of truth — geometry, colors, sizes
├── logos/
│   ├── svg/            ← source files, scale to any size
│   ├── png/            ← rasterized at standard sizes
│   ├── favicon/        ← favicon.svg, favicon.ico, touch + PWA icons
│   └── og/             ← link-preview cards
├── tokens/             ← palette + font stacks as CSS and JSON
├── fonts/              ← the OFL fonts the wordmark is cut from
├── social/             ← hand-made social images, PNG only (see below)
├── print/              ← print-ready PDFs (business cards)
└── _archive/           ← the files this repo replaced
```

### The brand in one table

| | |
|---|---|
| **Name** | YOLO Electronics Repair |
| **Handle** | `@yolo.repair` |
| **Tagline** | You let the smoke out. We put it back in. |
| **Solder-mask blue** | `#1E4D9B` |
| **Deep blue** | `#163D7E` |
| **Copper** | `#E0A050` |
| **Ink** (text on blue) | `#F3F2EE` |
| **Soft** (secondary text on blue) | `#D6DCEA` |
| **Display font** | Barlow Condensed, 600 / 800 |
| **Mono font** | IBM Plex Mono, 400 / 600 |

`BRANDING.md` has the reasoning and the rules. This is the cheat sheet.

### What's generated and what isn't

`logos/` and `tokens/` are build output — every file in them comes from
`brand.toml`. The other three asset folders are hand-made files, kept
as-is:

- **`social/`** — the round badge (`yolo-badge-1080.png`), the Facebook
  cover, and the original link-preview image. These only exist as PNGs.
  The badge's ring lettering and the circuit-trace corner decoration on
  the other two have no vector source, so they can't be regenerated or
  resized without redrawing them.
- **`print/`** — the Avery 5871 business card sheets, one with the pulse
  on the back and one with the Y-trace. The wordmark and pulse in
  `brand.toml` were measured off these.
- **`_archive/`** — the Y-trace drawings that were floating around
  before this repo: the two that were in the site, their PNG exports,
  and `yolo-mark-signature-240.png`, the one that got picked.
  `brand.toml` reproduces that PNG to within anti-aliasing. Nothing
  should link to this folder.

## Consuming the kit

For ad-hoc use, just grab a file (see *Quick start*). To consume the kit at a
**pinned version** — so a brand update can't silently restyle the site —
use a tagged release. Releases are versioned `vX.Y.Z` and listed on the
[Releases page](https://github.com/yolorepair/branding/releases); each one
ships a `.zip` / `.tar.gz` bundle of `logos/`, `tokens/`, `BRANDING.md`,
`preview.html`, and `LICENSE`.

**As a git submodule:**

<!-- x-release-please-start-version -->
```sh
git submodule add https://github.com/yolorepair/branding.git branding
git -C branding checkout v1.0.1      # pin to a release tag
git add branding && git commit       # the recorded submodule commit is your version pin
```
<!-- x-release-please-end -->

To move to a newer release later, check out the new tag inside the submodule
and commit the bump — a reviewable one-line diff.

**As a downloaded bundle:**

<!-- x-release-please-start-version -->
```sh
gh release download v1.0.1 --repo yolorepair/branding   # grabs the .zip + .tar.gz
```
<!-- x-release-please-end -->

**As a pinned image URL** — for a README or a page that embeds the logo over
HTTP without vendoring a copy. Pin to a release tag, never `main`: a tag is
immutable, so a brand update can't silently restyle your page.

<!-- x-release-please-start-version -->
```md
<img src="https://raw.githubusercontent.com/yolorepair/branding/v1.0.1/logos/svg/yolo-lockup.svg" alt="YOLO Electronics Repair" width="480">
```
<!-- x-release-please-end -->

Either way, the `logos/` directory layout and filenames are a stable contract
(see *Files* above), so a pin bump never moves assets out from under you.

## Developing the kit

Every asset in `logos/` and `tokens/` — and the tables in `BRANDING.md` — is
generated from `brand.toml`. Don't hand-edit the outputs; edit `brand.toml`
(or the prose in `BRANDING.md`) and rebuild.

```sh
make install     # one-time: install the Python build deps
make             # rebuild all SVGs, PNGs, favicons, tokens, and BRANDING.md tables
make help        # list every target
```

### Editing the brand

`brand.toml` is the single source of truth — colors, the trace geometry,
output sizes, and variants all live there. After editing it, run `make` and
commit the regenerated `logos/` and `tokens/` alongside your `brand.toml`
change.

Common tasks:

- **Add a raster size** — add the pixel value under the relevant
  `[sizes.*]` list, then `make`.
- **Change a color** — edit the hex in `[colors.board]` /
  `[colors.neutrals]`; `make` updates the assets, the tokens, and the
  `BRANDING.md` tables together.
- **Change the mark** — the trace path, stroke width, and pad sizes are
  plain numbers under `[mark]`. Change one, `make`, open `preview.html`.
- **Add a variant** — add a `[variants.<name>]` block (give it a
  `purpose` that names a real use), then `make`.

### Requirements

- Python 3.11+ (CI uses 3.12)
- [Cairo](https://www.cairographics.org) — `brew install cairo` on macOS,
  `libcairo2` on Debian/Ubuntu
- Nothing else. The fonts are vendored in `fonts/`, and `favicon.ico` is
  packed in pure Python.

### CI

CI re-runs `make` on every PR and fails if the committed `logos/`,
`tokens/`, or `BRANDING.md` drift from what `brand.toml` produces — so the
only way to change an asset is via `brand.toml` + `make`.

PNG bytes depend on the Cairo version that drew them. If CI says the PNGs
drifted and you didn't touch anything, rebuild in the same image CI uses:

```sh
docker run --rm -v "$PWD":/w -w /w ubuntu:24.04 sh -c 'apt-get update -qq && apt-get install -y -qq --no-install-recommends python3-pip python3-venv libcairo2 make >/dev/null && python3 -m venv /v && /v/bin/pip install -q -r requirements.txt && make PYTHON=/v/bin/python'
```

### Releases

Releases are automated with [release-please](https://github.com/googleapis/release-please).
Merging changes to `main` opens (or updates) a `chore(main): release X.Y.Z` PR
carrying the version bump and changelog; **merge that PR to cut the release** —
it tags `vX.Y.Z`, publishes the GitHub Release, and attaches the asset bundle.
There's no manual `git tag` or `gh release create`. Version bumps follow
Conventional Commits: `feat:` → minor, `fix:` → patch.

The same PR bumps the version in the pinning examples under *Consuming the
kit*. Those examples sit between `x-release-please` marker comments — leave
the markers alone and don't edit the version on those lines by hand.

## License

Three sets of terms, spelled out in [`LICENSE`](LICENSE):

- **Code** — the build scripts, `Makefile`, and CI config — is MIT.
- **The brand** — the YOLO Electronics Repair name, the marks, `brand.toml`,
  and everything generated or drawn from them — is the shop's own, all rights
  reserved. The files are here so the site and its tooling can fetch them,
  not as an invitation to reuse the logo.
- **The fonts** in `fonts/` are under the SIL Open Font License; their
  license files sit next to them.
