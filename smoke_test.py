import io
import pathlib
import py_compile
import sys
import tempfile

FILES = ("app.py", "catalogfix_core.py")

for name in FILES:
    path = pathlib.Path(name)
    if not path.exists():
        print(f"SMOKE FAIL: missing {name}")
        sys.exit(1)
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        print(f"SYNTAX FAIL: {name}: {exc}")
        sys.exit(1)

try:
    import catalogfix_core
    import fitz
    from pypdf import PdfWriter
except Exception as exc:
    print(f"IMPORT FAIL: {type(exc).__name__}: {exc}")
    sys.exit(1)

# Text/no-OCR route: exercises checkpoint setup, routing and return_meta plumbing.
try:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    with tempfile.TemporaryDirectory() as tmp:
        imported, report, meta = catalogfix_core.smart_import_pdf(
            buf,
            filename="smoke-no-ocr.pdf",
            checkpoint_dir=tmp,
            resume=False,
            return_meta=True,
            visual_ocr=False,
        )
    assert meta["total_pages"] == 1
    assert imported is not None
    assert report is not None
except Exception as exc:
    print(f"PDF SMOKE FAIL: {type(exc).__name__}: {exc}")
    sys.exit(1)

# Visual/OCR route: create a one-page PDF with no text layer and let the production
# PyMuPDF + RapidOCR path execute. It may find zero products, but must not error.
try:
    doc = fitz.open()
    doc.new_page(width=200, height=200)
    visual_bytes = doc.tobytes()
    doc.close()
    visual_buf = io.BytesIO(visual_bytes)
    with tempfile.TemporaryDirectory() as tmp:
        imported_v, report_v, meta_v = catalogfix_core.smart_import_pdf(
            visual_buf,
            filename="smoke-visual.pdf",
            checkpoint_dir=tmp,
            resume=False,
            return_meta=True,
            visual_ocr=True,
            ocr_dpi=100,
        )
    assert meta_v["total_pages"] == 1
    assert meta_v.get("visual_pages", 0) == 1
    if report_v is not None and not report_v.empty and "scan_status" in report_v.columns:
        statuses = " ".join(report_v["scan_status"].astype(str).tolist())
        assert "visual-error" not in statuses
        assert "visual-ocr-unavailable" not in statuses
except Exception as exc:
    print(f"VISUAL PDF SMOKE FAIL: {type(exc).__name__}: {exc}")
    sys.exit(1)

# Structured order-form route: generate enough trusted rows to exercise the
# order-form dominance threshold and suppression branch.
try:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    y = 72
    page.insert_text((50, y), "ORDER FORM", fontsize=12)
    y += 24
    page.insert_text((50, y), "ITEM NO     DESCRIPTION                       KIT PRICE     ASSEMBLED PRICE", fontsize=9)
    y += 18
    for n in range(1, 13):
        code = f"T{n:02d}"
        page.insert_text((50, y), f"{code:<10} TEST PRODUCT {n:<20} $ {100+n:.2f}       $ {200+n:.2f}", fontsize=8)
        y += 18
    order_bytes = doc.tobytes()
    doc.close()
    order_buf = io.BytesIO(order_bytes)
    with tempfile.TemporaryDirectory() as tmp:
        imported_o, report_o, meta_o = catalogfix_core.smart_import_pdf(
            order_buf,
            filename="smoke-order-form.pdf",
            checkpoint_dir=tmp,
            resume=False,
            return_meta=True,
            visual_ocr=False,
        )
    if imported_o is None or imported_o.empty:
        raise AssertionError("ORDER-FORM SMOKE: no products parsed")
    methods = set(imported_o["import_method"].astype(str))
    if "order-form-dual-price" not in methods:
        raise AssertionError(f"ORDER-FORM SMOKE: wrong methods {sorted(methods)}")
    if "quality_stats" not in meta_o:
        raise AssertionError("ORDER-FORM SMOKE: quality_stats missing")
except Exception as exc:
    print(f"ORDER-FORM SMOKE FAIL: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("OK: syntax + import + smart_import_pdf + visual OCR route + order-form route")
