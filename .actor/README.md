# CatalogFix AI — Safe Supplier Catalog Parser

**Clean supplier catalogs. Nothing invented, nothing guessed.**

CatalogFix AI converts supplier PDF, Excel and CSV files into normalized product data with an explicit **Ready / Needs Review** split.

The core principle is simple: **missing supplier data is flagged, not fabricated.** If a supplier SKU is not printed in the source, CatalogFix keeps that row review-only instead of creating a fake supplier code.

## What this Actor does

1. Accepts one PDF, CSV, XLSX or XLS catalog.
2. Routes PDF pages by content type and runs OCR only where needed.
3. Extracts structured and visual product records.
4. Applies quality gates and keeps source/audit context on every extracted row.
5. Returns structured Dataset rows plus downloadable audit files.

## Outputs

- **RESULT.xlsx** — full five-sheet workbook: Clean Master, Issues Found, Shopify Ready, Needs Review, Import Report.
- **SHOPIFY_READY.csv** — rows that passed the current release gates.
- **SUMMARY.json** — run counts and quality statistics.
- **IMPORT_REPORT.json** — routing and parsing audit information.
- **Dataset** — normalized product rows with source/quality context.

## Safety behavior

CatalogFix is designed to prefer an explicit review state over false certainty.

- Missing supplier SKUs are not invented.
- Internal candidate IDs remain review-only.
- Technical datasheets can be rejected with zero product rows instead of turning technical identifiers into products.
- Visual OCR keeps source location and confidence metadata for auditability.
- Structured price sources preserve price provenance where the parser has it.

**Knowing when not to extract is part of the product.**

## Input

Use the file-upload field to upload a supplier catalog or provide a direct URL.

Supported formats: PDF, CSV, XLSX, XLS.

For URLs that do not end in a recognizable extension, set **Filename override**.

## Example behavior

For an image-heavy supplier catalog, CatalogFix can recover printed supplier codes while keeping uncoded product cards in Needs Review.

For a technical datasheet, CatalogFix can intentionally return zero product rows with status **skipped-technical-datasheet**, instead of generating product records from engineering references.

## Current release

CatalogFix AI **v1.9.0**.

The current release includes adaptive visual OCR, structured commercial table and order-form parsing, Ready / Review quality gates, supplier-SKU-missing protection, a document-level technical-datasheet safety gate, and retained source/audit context.

## Notes

Processing time depends primarily on PDF page count and whether OCR is required. Image-heavy PDFs may trigger a second OCR pass on pages where the first pass does not provide enough commercial signal.

CatalogFix does not promise perfect extraction. It makes uncertainty explicit and keeps ambiguous rows out of Ready.


Deployment source: GitHub main branch.
