"""Statische export van de visualisatie (web/index.html).

De live app op `/` serveert web/template.html en haalt de graafdata via
GET /api/graph_data (W5.1). Dit script bakt een momentopname van diezelfde
data (viz_data.export_data) plus de gedeelde woordenschat in het template,
voor wie een statisch serveerbare kopie wil — bereikbaar als /static/index.html.
De kopie veroudert bij elke datawijziging; de live pagina niet.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import viz_data  # noqa: E402  (repo-root module, gedeeld met GET /api/graph_data)

OUT_PATH = Path(__file__).parent.parent / "web" / "index.html"
TEMPLATE_PATH = Path(__file__).parent.parent / "web" / "template.html"
SHARED_VOCAB_PATH = Path(__file__).parent.parent / "web" / "shared_vocab.js"
VOCAB_TAG = '<script src="/static/shared_vocab.js"></script>'


def generate():
    conn = sqlite3.connect(viz_data.DB_PATH)
    data = viz_data.export_data(conn)
    conn.close()

    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    # Gedeelde filter-woordenschat (web/shared_vocab.js) inlinen op de plek van de
    # script-tag, zodat de export niet uiteenloopt met de live pagina (zelfde bron).
    if VOCAB_TAG not in template:
        raise SystemExit(f"template.html mist de woordenschat-tag {VOCAB_TAG}")
    vocab = SHARED_VOCAB_PATH.read_text(encoding='utf-8')
    html = template.replace(VOCAB_TAG, '<script>\n' + vocab + '</script>')
    # Data in de boot-loader bakken: de sentinel "%%DATA%%" wordt het JSON-object,
    # waarna de loader de fetch naar /api/graph_data overslaat.
    if '"%%DATA%%"' not in html:
        raise SystemExit('template.html mist de "%%DATA%%" sentinel (boot-loader)')
    html = html.replace('"%%DATA%%"', json.dumps(data, ensure_ascii=False, indent=2))
    OUT_PATH.write_text(html, encoding='utf-8')
    print(f"Statische export gegenereerd: {OUT_PATH}")
    print(f"  {len(data['entities'])} entiteiten, {len(data['relations'])} relaties")
    print("  Live pagina (altijd actueel): http://localhost:5000/ — deze export: /static/index.html")


if __name__ == "__main__":
    generate()
