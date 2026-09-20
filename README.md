# CatalogFix AI v1.7 — Hybrid Quality Intelligence

Local Streamlit build for supplier CSV / Excel / PDF catalogs.

## v1.7 quality layer
- Universal page router: structured tables, price matrices, text-product pages, visual/image-heavy pages.
- Adaptive multi-pass OCR and visual-card fallback.
- Cross-page category context memory: specific category headings can be inherited by nearby continuation pages.
- Strict title cleanup: marketing prose is not used as a product title when a safer label/category is available.
- Quality Duplicate Killer for overlapping/repeated generated visual cards.
- Conservative dimension sanity checks with original/suggested values retained.
- Quality confidence + quality flags on every imported row.
- RAL/NCS protection: colour codes are not treated as supplier SKU.
- Missing supplier SKU or price is never invented; uncertain candidates stay review-only.
- Chunk autosave/resume for large PDFs. No artificial page-count limit.

## Start on Windows
Double-click `START_WINDOWS_CMD.bat`.

Then open the local Streamlit URL if the browser does not open automatically.

## Control test
For the same visual PDF used with v1.6.1, compare:
1. total candidates before/after quality pass;
2. duplicates removed;
3. inherited categories;
4. generic `Visual Catalog` count;
5. corrected dimensions;
6. weak-title / missing-supplier-SKU flags.

The goal is quality, not artificially increasing the number of rows.