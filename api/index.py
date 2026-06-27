"""Entrypoint Flask compatível com Vercel para o simulador IoT ESP32."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ROOT / "iot_eficiencia_energetica"

for path in (ROOT, API_DIR, PROJECT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from web_app import app as flask_app  # noqa: E402

app = flask_app
application = app
handler = app


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)