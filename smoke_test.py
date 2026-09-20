import pathlib
import py_compile
import sys

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
    import catalogfix_core  # noqa: F401
except Exception as exc:
    print(f"IMPORT FAIL: catalogfix_core: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("OK: syntax + import")
