# Manuscript

- **NewManuscript.docx** — main submission draft (figures embedded with `analysis/tumor/restore_manuscript_figures.py`).
- **CoAuthor_Profiles_NatureCommunications.docx** — one-page co-author profiles with institutional links.

Supplementary Word/Excel package: `analysis/tumor/supplementary/` (Figures 1–14 including decision schematic and KM panels).

To refresh embedded figures after re-running analyses:

```bash
cd analysis/tumor
cp ../../manuscript/NewManuscript.docx .
python restore_manuscript_figures.py
cp NewManuscript.docx ../../manuscript/
```
