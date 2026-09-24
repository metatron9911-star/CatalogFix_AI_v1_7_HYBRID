#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from actor_main import _import_catalog
from catalogfix_core import process_canonical, to_excel_bytes


def _records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = input_path.read_bytes()
    imported, import_report, pdf_meta, mapping, import_mode = _import_catalog(data, input_path.name)

    if imported.empty:
        summary = {
            "filename": input_path.name,
            "importMode": import_mode,
            "documentType": (pdf_meta or {}).get("document_type", "unknown"),
            "productRows": 0,
            "readyRows": 0,
            "reviewRows": 0,
            "issueRows": 0,
            "mappedFields": len(mapping),
        }
        (output_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        (output_dir / "IMPORT_REPORT.json").write_text(json.dumps(_records(import_report), indent=2, sort_keys=True), encoding="utf-8")
        return 0

    cleaned, issues, shop_ready, needs_review = process_canonical(imported)
    excel_result = to_excel_bytes(cleaned, issues, shop_ready, needs_review, import_report)

    (output_dir / "RESULT.xlsx").write_bytes(excel_result)
    (output_dir / "SHOPIFY_READY.csv").write_bytes(shop_ready.to_csv(index=False).encode("utf-8-sig"))
    (output_dir / "IMPORT_REPORT.json").write_text(json.dumps(_records(import_report), indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "CLEANED.json").write_text(json.dumps(_records(cleaned), indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "ISSUES.json").write_text(json.dumps(_records(issues), indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "NEEDS_REVIEW.json").write_text(json.dumps(_records(needs_review), indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "filename": input_path.name,
        "importMode": import_mode,
        "documentType": (pdf_meta or {}).get("document_type", "catalog-or-unknown"),
        "productRows": len(cleaned),
        "readyRows": len(shop_ready),
        "reviewRows": len(needs_review),
        "issueRows": len(issues),
        "mappedFields": len(mapping),
    }
    (output_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
