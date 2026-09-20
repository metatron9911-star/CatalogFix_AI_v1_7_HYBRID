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

print("OK: syntax + import + smart_import_pdf + visual OCR route")
