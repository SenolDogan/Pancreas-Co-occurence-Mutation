# Manuscript

- **NewManuscript.docx** — main submission draft (figures embedded with `analysis/tumor/restore_manuscript_figures.py`).

To refresh embedded figures after re-running analyses:

```bash
cd analysis/tumor
cp ../../manuscript/NewManuscript.docx .
python restore_manuscript_figures.py
cp NewManuscript.docx ../../manuscript/
```
