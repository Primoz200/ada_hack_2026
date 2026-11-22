"""Write contracts/openapi.json from the FastAPI app. Run from anywhere:
    uv run --project backend_turri python scripts/export_openapi.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend_turri"))

from app.main import app  # noqa: E402

out = ROOT / "contracts" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {out}")
