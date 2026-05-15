#!/usr/bin/env python3
"""
Build a single comparison table for sensitivity runs.

Input:
  Tumor/Stage_DX2Collection_Combo_OS_Interaction_Sensitivity.xlsx

Output:
  Tumor/Stage_DX2Collection_Interaction_Sensitivity_Comparison.xlsx
  Tumor/Stage_DX2Collection_Interaction_Sensitivity_Comparison.md
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


FILTERS = ["ALL", "DX_GE_0", "DX_0_TO_5"]
KEEP_COLS = [
    "Stage",
    "kind",
    "Feature",
    "n_pos",
    "n_neg",
    "HR_dx_x_adj",
    "p_int_adj",
    "p_int_adj_fdr_bh",
]


def load_filter_sheet(xlsx: Path, tag: str) -> pd.DataFrame:
    sh = f"All_{tag}"
    df = pd.read_excel(xlsx, sheet_name=sh)
    for c in KEEP_COLS:
        if c not in df.columns:
            df[c] = np.nan
    return df[KEEP_COLS].copy()


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    src = tumor_dir / "Stage_DX2Collection_Combo_OS_Interaction_Sensitivity.xlsx"
    out_xlsx = tumor_dir / "Stage_DX2Collection_Interaction_Sensitivity_Comparison.xlsx"
    out_md = tumor_dir / "Stage_DX2Collection_Interaction_Sensitivity_Comparison.md"

    frames = {}
    for tag in FILTERS:
        frames[tag] = load_filter_sheet(src, tag)
        frames[tag] = frames[tag].rename(
            columns={
                "HR_dx_x_adj": f"HR_int_adj_{tag}",
                "p_int_adj": f"p_int_adj_{tag}",
                "p_int_adj_fdr_bh": f"FDR_adj_{tag}",
            }
        )

    base = frames["ALL"][["Stage", "kind", "Feature"]].drop_duplicates()
    out = base.copy()

    # Merge n_pos/n_neg from ALL (for reference)
    nn = frames["ALL"][["Stage", "kind", "Feature", "n_pos", "n_neg"]].drop_duplicates()
    out = out.merge(nn, on=["Stage", "kind", "Feature"], how="left")

    for tag in FILTERS:
        cols = [c for c in frames[tag].columns if c.endswith(f"_{tag}")]
        out = out.merge(frames[tag][["Stage", "kind", "Feature", *cols]].drop_duplicates(), on=["Stage", "kind", "Feature"], how="left")

    # Add a simple stability flag: significant in ALL and remains <0.10 after dx_0_to_5
    out["stable_FDR_lt_0p10"] = (
        (out["FDR_adj_ALL"].notna() & (out["FDR_adj_ALL"] < 0.10))
        & (out["FDR_adj_DX_0_TO_5"].notna() & (out["FDR_adj_DX_0_TO_5"] < 0.10))
    )

    # Sort by ALL adjusted p within stage/kind
    out = out.sort_values(["Stage", "kind", "p_int_adj_ALL"], ascending=[True, True, True]).reset_index(drop=True)

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        out.to_excel(xw, sheet_name="Comparison_AllFilters", index=False)
        # Convenience: top rows per stage/kind
        for st in out["Stage"].dropna().unique().tolist():
            for k in ["pair", "triple"]:
                sdf = out[(out["Stage"] == st) & (out["kind"] == k)].head(50)
                if len(sdf) == 0:
                    continue
                name = f"{st[:12]}_{k}"
                name = name.replace(" ", "_").replace("/", "_")[:31]
                sdf.to_excel(xw, sheet_name=name, index=False)

    # Markdown snapshot: top 10 per stage/kind
    lines = []
    lines.append("# DX2COLLECTION_YEAR×combo interaction sensitivity — single comparison table\n\n")
    lines.append("Columns: HR_int_adj / p_int_adj / FDR_adj for each filter (ALL, DX_GE_0, DX_0_TO_5).\n\n")
    for st in out["Stage"].dropna().unique().tolist():
        lines.append(f"## {st}\n\n")
        for k in ["pair", "triple"]:
            sdf = out[(out["Stage"] == st) & (out["kind"] == k)].head(10).copy()
            if len(sdf) == 0:
                continue
            lines.append(f"### {k}\n\n")
            for _, r in sdf.iterrows():
                feat = str(r["Feature"])
                npos = int(r["n_pos"]) if pd.notna(r["n_pos"]) else -1
                stable = bool(r["stable_FDR_lt_0p10"])
                lines.append(
                    "- "
                    + f"**{feat}** (n_pos={npos}): "
                    + f"ALL HR={r['HR_int_adj_ALL']:.2f}, p={r['p_int_adj_ALL']:.3g}, FDR={r['FDR_adj_ALL']:.3g} | "
                    + f"DX_GE_0 HR={r['HR_int_adj_DX_GE_0']:.2f}, p={r['p_int_adj_DX_GE_0']:.3g}, FDR={r['FDR_adj_DX_GE_0']:.3g} | "
                    + f"DX_0_TO_5 HR={r['HR_int_adj_DX_0_TO_5']:.2f}, p={r['p_int_adj_DX_0_TO_5']:.3g}, FDR={r['FDR_adj_DX_0_TO_5']:.3g} "
                    + f"stable(FDR<0.10)={stable}\n"
                )
            lines.append("\n")
        lines.append("\n")

    out_md.write_text("".join(lines), encoding="utf-8")
    print(f"✅ Saved: {out_xlsx}")
    print(f"✅ Saved: {out_md}")


if __name__ == "__main__":
    main()

