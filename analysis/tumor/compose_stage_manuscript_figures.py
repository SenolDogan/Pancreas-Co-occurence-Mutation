#!/usr/bin/env python3
"""
Build composite PNGs used by NewManuscript.docx from upstream single-panel exports.

- Figure 3: Stage_OS_Effect_ForestPlot + Stage_ModelA_ModelB_ForestPlot (vertical stack)
- Figure 7: Panel A (top) + Panel B (bottom), native stack then **uniform** downscale to max width for Word (preserves aspect ratio).

Run after the respective generator scripts have written the source PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _scale_to_width(im: Image.Image, target_w: int) -> Image.Image:
    if im.width == target_w:
        return im
    h = max(1, int(round(im.height * target_w / im.width)))
    return im.resize((target_w, h), Image.Resampling.LANCZOS)


def _hstack_centered(left: Path, right: Path, out: Path, gap: int = 28, bg: tuple[int, int, int] = (255, 255, 255)) -> None:
    """Place two PNGs side by side at native resolution; vertically center the shorter panel."""
    im1 = Image.open(left).convert("RGBA")
    im2 = Image.open(right).convert("RGBA")
    h = max(im1.height, im2.height)
    w = im1.width + gap + im2.width
    canvas = Image.new("RGB", (w, h), bg)
    y1 = (h - im1.height) // 2
    y2 = (h - im2.height) // 2
    canvas.paste(im1.convert("RGB"), (0, y1))
    canvas.paste(im2.convert("RGB"), (im1.width + gap, y2))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, dpi=(350, 350))


def _vstack_same_width(top: Path, bottom: Path, out: Path, gap: int = 24) -> None:
    im1 = Image.open(top).convert("RGBA")
    im2 = Image.open(bottom).convert("RGBA")
    w = max(im1.width, im2.width)
    a = _scale_to_width(im1, w)
    b = _scale_to_width(im2, w)
    h = a.height + gap + b.height
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    canvas.paste(a.convert("RGB"), (0, 0))
    canvas.paste(b.convert("RGB"), (0, a.height + gap))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, dpi=(350, 350))


def compose_figure3(tumor_dir: Path) -> None:
    top = tumor_dir / "Stage_OS_Effect_ForestPlot.png"
    bot = tumor_dir / "Stage_ModelA_ModelB_ForestPlot.png"
    out = tumor_dir / "Stage_Figure2_AB_ForestPlots_VSTACK.png"
    if not top.is_file() or not bot.is_file():
        print(f"⚠️  Skip Figure 3 composite (missing {top.name} or {bot.name})")
        return
    _vstack_same_width(top, bot, out)
    print(f"✅ Wrote {out.name}")


def _panel_letter_font(size: int):
    """Bold-ish sans font for A/B panel tags; fall back to default bitmap font."""
    paths: list[tuple[str, int | None]] = [
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", None),
        ("/System/Library/Fonts/Helvetica.ttc", 1),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", None),
    ]
    for path, idx in paths:
        try:
            if idx is not None:
                return ImageFont.truetype(path, size, index=idx)
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# Max width for Figure 7 composite export: very wide matplotlib PNGs (~4800px) distort in Word when
# squeezed to ~6.8in; uniform downscale keeps aspect ratio and restores legible text.
FIG7_EXPORT_MAX_WIDTH_PX = 2000


def _vstack_figure7_ab_labels(top: Path, bottom: Path, out: Path, gap: int = 24) -> None:
    """Panel A on top, Panel B below; native paste + horizontal center; uniform export resize for Word."""
    a = Image.open(top).convert("RGBA")
    b = Image.open(bottom).convert("RGBA")
    w0 = max(a.width, b.width)
    h0 = a.height + gap + b.height
    xa0 = (w0 - a.width) // 2
    xb0 = (w0 - b.width) // 2
    ya0, yb0 = 0, a.height + gap

    canvas = Image.new("RGBA", (w0, h0), (255, 255, 255, 255))
    canvas.paste(a, (xa0, ya0))
    canvas.paste(b, (xb0, yb0))

    sc = min(1.0, FIG7_EXPORT_MAX_WIDTH_PX / float(w0))
    if sc < 1.0:
        nw, nh = int(round(w0 * sc)), int(round(h0 * sc))
        canvas = canvas.resize((nw, nh), Image.Resampling.LANCZOS)
        xa = int(round(xa0 * nw / w0))
        ya = int(round(ya0 * nh / h0))
        xb = int(round(xb0 * nw / w0))
        yb = int(round(yb0 * nh / h0))
        w, h = nw, nh
    else:
        w, h, xa, ya, xb, yb = w0, h0, xa0, ya0, xb0, yb0

    font = _panel_letter_font(max(16, min(32, w // 28)))
    draw = ImageDraw.Draw(canvas)
    margin = max(8, w // 100)
    ax_text, ay_text = xa + margin, ya + margin
    bx_text, by_text = xb + margin, yb + margin
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        draw.text((ax_text + dx, ay_text + dy), "A", font=font, fill=(255, 255, 255))
    draw.text((ax_text, ay_text), "A", font=font, fill=(0, 0, 0))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        draw.text((bx_text + dx, by_text + dy), "B", font=font, fill=(255, 255, 255))
    draw.text((bx_text, by_text), "B", font=font, fill=(0, 0, 0))

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, dpi=(300, 300))


def compose_figure7(tumor_dir: Path) -> None:
    top = tumor_dir / "Stage_Pair_Additive_TopBars.png"
    bottom = tumor_dir / "Stage_Cox_Pairs_TopForest.png"
    out = tumor_dir / "Stage_Figure6_AB_AdditiveBars_CoxPairsForest.png"
    if not top.is_file() or not bottom.is_file():
        print(f"⚠️  Skip Figure 7 composite (missing {top.name} or {bottom.name})")
        return
    _vstack_figure7_ab_labels(top, bottom, out)
    im = Image.open(out)
    print(f"✅ Wrote {out.name} ({im.width}×{im.height}px)")


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if mode in ("all", "fig3", "3"):
        compose_figure3(tumor_dir)
    if mode in ("all", "fig7", "7"):
        compose_figure7(tumor_dir)


if __name__ == "__main__":
    main()
