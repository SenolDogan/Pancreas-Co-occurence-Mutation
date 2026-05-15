#!/usr/bin/env python3
"""
Replace embedded PNG figures in NewManuscript.docx with on-disk versions.

Only binary image parts under word/media/ are updated; document.xml, tables,
paragraphs, and styles are left unchanged.

Figure order must match build_new_manuscript.py (same as document picture order).

CLI: pass --figure2 or --figure7 to replace only that embedded PNG (Figure 2 / Figure 7 in manuscript order).
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches


def _fix_inline_shape_extent_for_media(
    docx_path: Path,
    *,
    png_path: Path,
    media_rel_suffix: str = "media/image7.png",
    max_width_in: float = 6.8,
    max_height_in: float = 9.0,
) -> bool:
    """
    After raw ZIP replacement of a PNG, Word still uses old wp:extent (cx/cy) on the drawing.
    Set the inline picture's width/height from the actual PNG aspect ratio so the figure is not stretched.
    """
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow not installed; cannot adjust Word picture extents.")
        return False

    if not png_path.is_file():
        print(f"⚠️  Missing PNG for extent fix: {png_path}")
        return False

    w_px, h_px = Image.open(png_path).size
    if w_px <= 0 or h_px <= 0:
        return False
    aspect = w_px / h_px

    doc = Document(str(docx_path))
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    for shape in doc.inline_shapes:
        rid = None
        for el in shape._inline.iter():
            if el.tag == A + "blip":
                rid = el.get(qn("r:embed"))
                break
        if not rid:
            continue
        rel = doc.part.rels[rid]
        tr = str(rel.target_ref).replace("\\", "/")
        if not tr.endswith(media_rel_suffix):
            continue
        mw, mh = max_width_in, max_height_in
        h_if_full_w = mw / aspect
        if h_if_full_w <= mh:
            outer_w, outer_h = mw, h_if_full_w
        else:
            outer_h = mh
            outer_w = mh * aspect
        shape.width = Inches(outer_w)
        shape.height = Inches(outer_h)
        doc.save(str(docx_path))
        print(
            f"  ✅ Word extent fixed for {media_rel_suffix} "
            f"→ {outer_w:.2f}×{outer_h:.2f} in (PNG {w_px}×{h_px}, aspect {aspect:.3f})"
        )
        return True

    print(f"⚠️  No inline picture found for {media_rel_suffix}; extent not updated.")
    return False


def _figure_sources(tumor_dir: Path) -> list[Path]:
    new2 = tumor_dir.parent
    t = tumor_dir
    return [
        new2 / "01_Dead_Alive_Comprehensive_Analysis.png",
        t / "Stage_3Group_Comprehensive_Analysis.png",
        t / "Stage_Figure2_AB_ForestPlots_VSTACK.png",
        t / "Stage_06_OS_Months_Methodology_Analysis.png",
        t / "Stage_05_TP53_KRAS_Detailed_Analysis.png",
        t / "Stage_02_TP53_KRAS_Focused_Analysis.png",
        t / "Stage_Figure6_AB_AdditiveBars_CoxPairsForest.png",
        t / "Stage_Triple_Additive_TopBars.png",
        t / "Stage_Cox_Triples_TopForest.png",
        t / "Stage_DX2Collection_Pair_Interaction_Volcano_DX_GE_0.png",
        t / "Stage_DX2Collection_Triple_Interaction_Volcano_DX_GE_0.png",
        t / "Stage_12_TP53_KRAS_ShortSurvival_Comparison.png",
        t / "Stage_14_Diabetic_vs_NonDiabetic_Gene_Analysis.png",
        t / "Stage_DX2Collection_Triple_Interaction_Volcano_DX_0_TO_5.png",
    ]


def _media_png_members(z: zipfile.ZipFile) -> list[str]:
    names = sorted(
        [n for n in z.namelist() if n.startswith("word/media/") and n.lower().endswith(".png")],
        key=lambda x: int(m.group(1)) if (m := re.search(r"image(\d+)\.png$", x, re.I)) else 0,
    )
    return names


def update_newmanuscript_figures_only(
    docx_path: Path | None = None,
    *,
    only_figure_indices: set[int] | None = None,
) -> bool:
    """
    Replace embedded PNGs in NewManuscript.docx.

    only_figure_indices: if set, 1-based indices matching _figure_sources order (e.g. {2} = Figure 2 / image2.png only).
    """
    tumor_dir = Path(__file__).resolve().parent
    docx_path = docx_path or (tumor_dir / "NewManuscript.docx")
    sources = _figure_sources(tumor_dir)

    if not docx_path.is_file():
        print(f"❌ Missing: {docx_path}")
        return False

    tmp_path = docx_path.with_suffix(".tmp.docx")

    with zipfile.ZipFile(docx_path, "r") as zin:
        media_members = _media_png_members(zin)
        if len(media_members) != len(sources):
            print(
                f"❌ Expected {len(sources)} PNG parts in word/media/, found {len(media_members)}. "
                "Aborting to avoid misaligned replacements."
            )
            print("  Media:", media_members)
            return False

        replacements: dict[str, bytes] = {}
        replacement_sources: dict[str, Path] = {}
        for idx, (arcname, src) in enumerate(zip(media_members, sources), start=1):
            if only_figure_indices is not None and idx not in only_figure_indices:
                continue
            if not src.is_file():
                print(f"⚠️  Skip (missing source): {arcname} <- {src}")
                continue
            replacements[arcname] = src.read_bytes()
            replacement_sources[arcname] = src
            print(f"  ✅ {arcname} <- {src.name}")

        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename in replacements:
                    data = replacements[info.filename]
                zout.writestr(info, data)

    tmp_path.replace(docx_path)

    # Figure 7 is a tall vertical composite; raw PNG replace leaves old wide wp:extent → stretch/squash.
    arc7 = "word/media/image7.png"
    if arc7 in replacement_sources:
        _fix_inline_shape_extent_for_media(
            docx_path,
            png_path=replacement_sources[arc7],
            media_rel_suffix="media/image7.png",
        )

    print(f"\n✅ Updated figures only: {docx_path}")
    return True


if __name__ == "__main__":
    only: set[int] | None = None
    if "--figure2" in sys.argv:
        only = {2}
        print("Mode: replace embedded Figure 2 (image2.png) only.")
    elif "--figure7" in sys.argv:
        only = {7}
        print("Mode: replace embedded Figure 7 (image7.png) only.")
    raise SystemExit(0 if update_newmanuscript_figures_only(only_figure_indices=only) else 1)
