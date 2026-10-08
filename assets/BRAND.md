# Crew Book brand rule

One rule for every asset, so the logo, the icons, the README banner and the
social preview look like one product (#88). The rule is derived from
workharbor's `assets/BRAND.md`: the same tile, colours, type and lockup
geometry, with a different mark. Name and casing: the package, skill and paths
are `crewbook`; only the wordmark and reader-facing prose use **Crew Book**.

## The mark

A guide star over an open book. The book is drawn in teal strokes (width 4 in
the 64-unit box, round caps and joins); the star is a **filled** teal shape
with sharp points, not a stroke, and sits above the book's spine. The two
parts are never redrawn in the other style.

## Two forms, never mixed

- **App icon** (square places only: `logo.svg`/`logo.png`, `favicon.svg`,
  `favicon.ico`, `apple-touch-icon.png`): the teal mark on a rounded navy tile.
  Tile corner radius 13.28 units in the 64-unit box (workharbor's tile); the
  mark's drawn height 70 % of the side (47 units scaled by 0.95319), centred,
  so it stays legible at 16 px. Every rounded tile has a visible outline: 1.6 units in the 64-unit
  box (2.5 % of the side), colour `#2a4a7a`, drawn inside the tile's edge.
- **Horizontal lockup** (any wide place): the bare teal mark, no tile, then
  the wordmark. A lockup never appears in a square place, and a tile never
  appears in a lockup, except as listed below.

## Exceptions

1. **Tile lockup in the README banner and the social preview.** As in
   workharbor (#143), these two assets show the mark on its rounded tile beside
   the wordmark and the tagline: 96 px in the banner (64 units at scale 1.5),
   288 px in the social preview (scale 4.5).
2. **Background gradient.** The banner and the social preview use workharbor's
   diagonal gradient from navy `#0b2545` to `#13315c`. It is the only gradient,
   and `#13315c` appears nowhere else.
3. **`apple-touch-icon.png`** is an opaque, full-bleed navy square with no
   rounded corners, no outline and no transparency, because iOS applies its own
   mask and fills transparent pixels with black.
4. **Stroke and fill.** Unlike workharbor's all-stroke anchor, the star is a
   filled shape beside the book's strokes (see The mark).
5. **Two words.** The wordmark has a space ("Crew Book"); workharbor's is one
   word. The social preview carries no third line.

## The lockup, in proportions of the wordmark's cap height C

| Element | Rule |
| --- | --- |
| Wordmark | "Crew Book" in Bricolage Grotesque Bold (wght 700, no added letter spacing), outlined: "Crew" in the text colour, "Book" in teal; cap height 0.66 × font size |
| Mark, tile lockup | tile 2.14 × C in the banner, 4.36 × C in the social preview; the wordmark's ink starts about 0.8 × C to the right of the tile |
| Mark, bare lockup | drawn height 2.4 × C, vertically centred on the wordmark's cap height; book stroke 5.5 in the 64-unit drawing; gap to the wordmark 0.6 × C |
| Tagline | "Guidance and workflow for coding agents.", IBM Plex Sans Regular, outlined, teal, left-aligned with the wordmark (its origin 3.5 px right of the wordmark's origin in the banner, 4 px in the social preview) |
| Clear space | at least 0.45 × C above and below the whole block (tile and text); in the README banner the tile leaves 27 px, 0.6 × C, at top and bottom |

The banner and social preview reuse workharbor's exact positions and sizes, so
"Crew Book" and "WorkHarbor" sit at the same scale, baseline and spacing.

## Sizes

| Asset | Size | Wordmark | Tagline |
| --- | --- | --- | --- |
| README banner | 1000 × 150, rounded 18 px; tile at (56, 27) | 68 px (optical size 72), C = 44.9 px, baseline 80, ink from x 187.08 | 30 px, baseline 118 (0.85 × C below) |
| Social preview | 1280 × 640; tile at y 184, the whole block centred horizontally | 100 px (optical size 96), C = 66 px, baseline 318 | 36 px, baseline 388 (1.06 × C below) |
| `logo.png` | 512 × 512, from `logo.svg` | none | none |
| `favicon.ico` | 16, 32 and 48 px, from `favicon.svg` | none | none |
| `apple-touch-icon.png` | 180 × 180, full bleed | none | none |

## Colours

Navy `#0b2545` background with white text and teal `#5eead4`; on a light
background, navy `#0b2545` text and deep teal `#0f766e`. Tile outline
`#2a4a7a`. No other colours, except the gradient stop in Exception 2.

## Fonts

Bricolage Grotesque and IBM Plex Sans are licensed under the SIL Open Font
License 1.1. Every asset carries them only as outlines, so no font file ships
in this repository. The font files and their licence texts are those of
workharbor: `assets/fonts/bricolage-grotesque/` (variable TTF and `OFL.txt`)
and `docs/static/fonts/ibm-plex-sans/` (`OFL.txt`).

Every asset is regenerated from its SVG; a PNG or ICO is never edited by hand.
A change to this rule, or to an asset, is shown to Werner as one comparison
image of all assets before it lands.
