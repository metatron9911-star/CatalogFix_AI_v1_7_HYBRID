# CatalogFix AI v1.8.12 — Hybrid Quality Intelligence

CatalogFix converts supplier CSV, Excel and PDF catalogues into a normalized product master, QA report, and safe Shopify-ready export.

## Core routing
- Universal PDF router: `VISUAL`, `STRUCTURED_PRICE`, `TEXT_PRODUCT`, `TEXT_OTHER`.
- Adaptive multi-pass OCR for image-heavy catalogues.
- Structured parsers for standard SKU/description/price tables, dual-price order forms, vehicle multi-price lists, tiered service tables, matrices, and brochure-style price cards.
- Technical datasheets and statistical price reports are safety-gated to 0 product rows instead of generating false products.

## Quality Intelligence
- Cross-page category context memory.
- Conservative title repair and PDF text sanity checks.
- Duplicate suppression across structured and visual candidates.
- Dimension sanity checks with original/suggested values retained.
- RAL/NCS protection.
- `quality_confidence`, `quality_flags`, `visual_confidence`, and `router_type` retained for auditability.
- Missing supplier SKU or price is never silently invented. Review-only rows use internal `CAND-...` identifiers and carry `supplier_sku_missing`.

## Price provenance
When a source exposes more than one price, the chosen export price is explicit and alternate source prices are preserved in `attributes_json`. Examples include:
- IMSAI `kit_price` + `assembled_price`;
- vehicle `basic_price`, VAT, retail and OTR fields;
- regional/service price tiers.

## Image-only PDFs
PDFs without a usable text layer route to visual OCR when PyMuPDF/OCR dependencies are available. If visual OCR is unavailable, the import report records `visual-ocr-unavailable` rather than raising an exception.

## Large PDFs
CatalogFix writes resumable gzip checkpoints and a versioned `manifest.json`. Checkpoints are intentionally invalidated when the processing version changes, so quality-rule changes trigger a clean rescan.

## Railway
The included `railway.toml` starts Streamlit on Railway's `$PORT`.

## Output
- Clean Master
- Issues Found
- Shopify Ready
- Needs Review
- Import Report


## Document-level safety gate
The safety gate is heuristic and document-scoped. If a representative sample looks like a technical datasheet or statistical report, CatalogFix performs a second lightweight page-by-page commercial-signal probe before rejecting the whole file. This is designed to preserve hybrid PDFs that contain a genuine price list somewhere outside the initial sample.


## Full-document commercial probe
When the representative sample looks like a technical datasheet or statistical report, CatalogFix performs a lightweight page-by-page text probe for commercial markers. The probe does not retain page text in memory and stops immediately at the first genuine commercial signal. If no commercial signal is found anywhere in the document, the whole file is rejected before OCR/product extraction.

## Checkpoint compatibility
Checkpoint manifests are version-gated. Checkpoints created by v1.8.11 are intentionally not reused by v1.8.12 or later; the first run after a processing-version change performs a clean rescan. Resume/reproducibility should therefore be validated with two runs of the same version.
