import io
from pathlib import Path

import pandas as pd
import streamlit as st

from catalogfix_core import (
    CANONICAL_FIELDS,
    map_columns,
    process_canonical,
    smart_import_excel,
    smart_import_pdf,
    standard_import_dataframe,
    to_excel_bytes,
)

st.set_page_config(page_title="CatalogFix AI v1.8.15", page_icon="🧹", layout="wide")
st.title("CatalogFix AI v1.8.15")
st.caption("Hybrid Quality Intelligence: universal routing + visual layout intelligence + context memory + dedupe + sanity checks + QA")

st.info("Hybrid Quality Intelligence is ON: universal page routing + multi-pass visual OCR + page-context category memory + conservative dimension sanity checks + visual duplicate suppression + confidence/QA. Large PDFs autosave and resume after interruption.")

uploaded = st.file_uploader("Upload supplier CSV / Excel / PDF", type=["csv", "xlsx", "xls", "pdf"])

if not uploaded:
    st.info("Upload CSV, Excel or PDF. v1.8 routes text tables, matrices and visual catalogs, then applies cross-page Quality Intelligence. Candidates without a printed supplier SKU stay review-only. Missing prices are never invented.")
    st.stop()

filename = uploaded.name
name_l = filename.lower()

try:
    if name_l.endswith(".csv"):
        source_df = pd.read_csv(uploaded, dtype=object)
        imported, mapping = standard_import_dataframe(source_df)
        import_report = pd.DataFrame([{
            "sheet": "CSV",
            "source_rows": len(source_df),
            "source_columns": len(source_df.columns),
            "header_products": len(imported),
            "pattern_products": 0,
            "matrix_products": 0,
        }])
        import_mode = "Standard columns"
    elif name_l.endswith(".pdf"):
        uploaded.seek(0)
        progress = st.progress(0, text="Scanning PDF pages…")
        def _progress(stage, current, total):
            frac = (0.35 * current / max(total, 1)) if stage == "scan" else (0.35 + 0.65 * current / max(total, 1))
            label = "Routing all PDF pages" if stage == "scan" else "Parsing routed product pages"
            progress.progress(min(frac, 1.0), text=f"{label}: {current}/{total}")
        checkpoint_root = Path(__file__).resolve().parent / "CatalogFix_Checkpoints"
        imported, import_report, pdf_meta = smart_import_pdf(
            uploaded,
            filename=filename,
            progress_callback=_progress,
            chunk_size=100,
            checkpoint_dir=checkpoint_root,
            resume=True,
            return_meta=True,
        )
        progress.empty()
        mapping = {field: field for field in CANONICAL_FIELDS if field in imported.columns}
        import_mode = "Universal PDF Router"
    else:
        # First attempt a normal sheet read. If enough canonical fields are obvious,
        # keep the fast v1.0 path; otherwise switch to Smart Import.
        uploaded.seek(0)
        standard_df = pd.read_excel(uploaded, dtype=object)
        standard_mapping = map_columns([str(c) for c in standard_df.columns])

        if len(standard_mapping) >= 3 and ("sku" in standard_mapping or "title" in standard_mapping):
            imported, mapping = standard_import_dataframe(standard_df)
            import_report = pd.DataFrame([{
                "sheet": "First sheet",
                "source_rows": len(standard_df),
                "source_columns": len(standard_df.columns),
                "matrix_products": 0,
                "header_products": len(imported),
                "pattern_products": 0,
            }])
            import_mode = "Standard columns"
        else:
            uploaded.seek(0)
            imported, import_report = smart_import_excel(uploaded, filename=filename)
            mapping = {field: field for field in CANONICAL_FIELDS if field in imported.columns}
            import_mode = "Smart Import"
except Exception as exc:
    st.error(f"Could not read/import file: {exc}")
    st.stop()

if imported.empty:
    if name_l.endswith(".pdf") and (pdf_meta or {}).get("document_type") in {"technical-datasheet","statistical-report"}:
        dtype=(pdf_meta or {}).get("document_type")
        if dtype=="technical-datasheet":
            st.warning("Technical datasheet / engineering manual detected. CatalogFix intentionally created 0 product rows because no commercial price catalog was found.")
        else:
            st.warning("Statistical / analytical price report detected. CatalogFix intentionally created 0 product rows because this is not a supplier product catalogue.")
        st.caption(f"Pages checked: {pdf_meta.get('total_pages', 0)} • safety gate: {dtype}")
        st.dataframe(import_report, use_container_width=True)
        st.stop()
    if name_l.endswith(".pdf") and (pdf_meta or {}).get("document_type") == "unknown":
        st.warning("No product rows were detected from the PDF text layer. This usually means the file is image-only or has no usable embedded text, so OCR/visual routing is required.")
        st.dataframe(import_report, use_container_width=True)
        st.stop()
    st.error("No product-like rows were detected. This file needs another importer rule.")
    st.stop()

cleaned, issues, shop_ready, needs_review = process_canonical(imported)
critical_count = 0 if issues.empty else int((issues["severity"] == "Critical").sum())
ready_count = int((cleaned["qa_status"] == "READY").sum())

st.success(f"Import mode: {import_mode}. Detected {len(cleaned)} product row(s).")

if name_l.endswith(".pdf"):
    st.caption(
        f"Autosave: every {pdf_meta['chunk_size']} pages • "
        f"Pages: {pdf_meta['total_pages']} • "
        f"Routed pages: {pdf_meta['candidate_pages']} • "
        f"Visual: {pdf_meta.get('visual_pages', 0)} • "
        f"Structured: {pdf_meta.get('structured_pages', 0)} • "
        f"Resumed chunks: {pdf_meta['resumed_chunks']}"
    )
    st.caption(f"Checkpoint folder: {pdf_meta['checkpoint_folder']}")
    qs = pdf_meta.get("quality_stats", {}) or {}
    if qs:
        st.subheader("Quality Intelligence")
        q1,q2,q3,q4,q5,q6,q7 = st.columns(7)
        q1.metric("Input candidates", qs.get("input_rows", 0))
        q2.metric("After quality pass", qs.get("output_rows", 0))
        q3.metric("Duplicates removed", qs.get("duplicates_removed", 0))
        q4.metric("Categories inferred", qs.get("categories_inferred", 0))
        q5.metric("Categories inherited", qs.get("categories_inherited", 0))
        q6.metric("Brands inferred", qs.get("brands_inferred", 0))
        q7.metric("Titles trimmed", qs.get("body_tails_trimmed", 0))
        if qs.get("invariant_input_output_mismatch"):
            st.error(f"Quality invariant mismatch: delta={qs.get('invariant_delta', 0)}")
        else:
            st.caption("Quality invariant OK: input_rows = output_rows + duplicates_removed")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Products detected", len(cleaned))
c2.metric("Issues", len(issues))
c3.metric("Critical", critical_count)
c4.metric("Ready for Shopify", ready_count)
c5.metric("Mapped fields", len(mapping))

with st.expander("Import report", expanded=False):
    st.dataframe(import_report, use_container_width=True)

st.subheader("Smart Import preview")
preview_cols = [c for c in [
    "sku", "supplier_code", "title", "brand", "price", "category", "size",
    "matrix_series", "matrix_section", "matrix_model", "variant_codes",
    "source_page", "source_sheet", "source_row", "import_confidence", "visual_confidence", "quality_confidence", "quality_flags", "category_source", "router_type", "import_method"
] if c in cleaned.columns]
st.dataframe(cleaned[preview_cols].head(100), use_container_width=True)

st.subheader("Clean Master")
st.dataframe(cleaned.head(100), use_container_width=True)

st.subheader("Issues Found")
if issues.empty:
    st.success("No obvious issues found.")
else:
    st.dataframe(issues.head(1000), use_container_width=True)

st.subheader("Shopify Ready")
if shop_ready.empty:
    st.warning("No rows are safe to export yet. For catalogs without prices this is expected: missing price is Critical.")
else:
    st.success(f"{len(shop_ready)} row(s) passed critical validation and are safe for export.")
    st.dataframe(shop_ready.head(100), use_container_width=True)

if not needs_review.empty:
    with st.expander(f"Needs Review ({len(needs_review)} rows)", expanded=False):
        st.dataframe(needs_review.head(500), use_container_width=True)

excel_result = to_excel_bytes(cleaned, issues, shop_ready, needs_review, import_report)
st.download_button(
    "Download full result (.xlsx)",
    excel_result,
    file_name="CatalogFix_Result_v1_8_15.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.download_button(
    "Download safe Shopify-ready CSV",
    shop_ready.to_csv(index=False).encode("utf-8-sig"),
    file_name="Shopify_Ready_v1_8_15.csv",
    mime="text/csv",
    disabled=shop_ready.empty,
)