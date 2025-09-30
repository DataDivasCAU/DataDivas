from __future__ import annotations
from flask import Flask, render_template, jsonify, send_file, abort, request
from pathlib import Path
from io import BytesIO
import json
from party import Party, fetch_channel_statistics

# ⬅️ externe Export-Funktionen (liegen in /templates, aber nicht Teil von Flask-Templates!)
from templates.election_export_xlsx import build_workbook
from templates.election_export_pdf import build_pdf

# Flask-App initialisieren
app = Flask(__name__)
# JSON-Ausgabe: Keys in Original-Reihenfolge erhalten
app.json.sort_keys = False

# ----------------- PFADKONSTANTEN -----------------
# Basisverzeichnis (dort, wo app.py liegt)
BASE = Path(__file__).resolve().parent
# Datenquellen für Posts, Wahlen, Fridays for Future, AfD usw.
DATA_PATH          = "data/postPerParty/data.json"
ELECTION_PATH      = "data/postPerParty/election.json"
DATA_CSV_PATH      = BASE / "data" / "postPerParty" / "data.csv"
ELECTION_CSV_PATH  = BASE / "data" / "postPerParty" / "election.csv"
FRIDAYS_JSON_PATH  = BASE / "data" / "fridaysForFuture" / "fridaysForFuture.json"
FFF_STRIKES_CSV_PATH = BASE / "data" / "fridaysForFuture" / "fff_germany_strikes.csv"
AFD_COMBINED_JSON_PATH = BASE / "data" / "afd" / "AfD_combined_relative.json"
AFD_DAILY_JSON_PATH    = BASE / "data" / "afd" / "AfD_combined_daily_relative.json"

# ----------------- HILFSFUNKTIONEN -----------------
def load_json(path: str):
    """Hilfsfunktion: JSON-Datei laden und als Python-Dict zurückgeben.
    Fehler (Datei fehlt / JSON kaputt) führen zu HTTP-Fehlern.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        abort(404, description=f"Datei nicht gefunden: {path}")
    except json.JSONDecodeError as e:
        abort(500, description=f"JSON-Fehler in {path}: {e}")

# ----------------- BASIS-ROUTEN -----------------
@app.route("/")
def index():
    # Startseite
    return render_template("index.html")

# Beispiel: einzelne Seiten-Templates
@app.route("/post-per-party")
def post_per_party():
    return render_template("post-per-party.html")

@app.route("/post-per-party/stats")
def post_per_party_stats():
    # Tabelle und Diagramm zu aktuellen YouTube-Parteidaten
    return render_template("stats.html")

@app.route("/antivax-yt")
def antivax():
    return render_template("antivax.html")

# ----------------- JSON-ENDPUNKTE -----------------
# Beispiel: Antivax-Daten
@app.route("/answer_one.json")
def antivax_answer_one():
    path = Path(BASE) / "data" / "antivax" / "answer_one.json"
    return jsonify(load_json(str(path)))

# AfD-Endpoints, FridaysForFuture, Wagenknecht etc.
# → laden JSON-Dateien aus dem data/-Ordner und geben sie als API zurück
# → bei Fehlern: HTTP 404 oder 500
# (hier viele Wiederholungen mit identischem Muster)

# Besonderheit: /fff_strikes.json liest eine CSV-Datei und filtert gültige Datumsstrings heraus.

# Besonderheit: /wagenknecht_words_combined.json fasst zwei JSON-Dateien zusammen
# (Wortlisten A und B) und aggregiert die Worthäufigkeiten.

# ----------------- PARTEI-YOUTUBE-STATS -----------------
@app.route("/load_yt_current_data_of_parties")
def channel_stats_all():
    """Lädt aktuelle YouTube-Statistiken aller Parteien über fetch_channel_statistics.
    Ergebnis: Liste mit einem Eintrag pro Partei inkl. Zeitstempel.
    Speichert zusätzlich unter data/postPerParty/stats.json
    """
    from datetime import datetime
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for party in Party:
        try:
            stats = fetch_channel_statistics(party)
            stats["timestamp"] = timestamp
            results.append(stats)
        except Exception as e:
            # Falls API-Quota oder Fehler: Eintrag mit Fehlerdetails
            results.append({
                "party": party.value,
                "error": "konnte nicht geladen werden",
                "details": str(e),
                "timestamp": timestamp
            })

    # Versuch, Ergebnis lokal als stats.json zu speichern (Fehler werden ignoriert)
    try:
        stats_path = BASE / "data" / "postPerParty" / "stats.json"
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return jsonify(results)

@app.route("/export-current-stats.json")
def export_current_stats_json():
    """Wie oben, aber direkter JSON-Download (ohne Datei schreiben)."""
    results = []
    for party in Party:
        try:
            results.append(fetch_channel_statistics(party))
        except Exception as e:
            results.append({"party": party.value, "error": str(e)})

    resp = jsonify(results)
    resp.headers["Content-Disposition"] = "attachment; filename=current_party_stats.json"
    return resp

# ----------------- EXPORT-FUNKTIONEN -----------------
@app.route("/export-excel")
def export_excel():
    """Posts + Wahldaten als Excel exportieren (XLSX im Speicher bauen)."""
    try:
        posts_data    = load_json(DATA_PATH)
        election_data = load_json(ELECTION_PATH)
        xlsx_io: BytesIO = build_workbook(posts_data, election_data)
        xlsx_io.seek(0)
        return send_file(
            xlsx_io,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="posts-per-party_all.xlsx",
        )
    except Exception as e:
        abort(500, description=f"Export-Fehler: {type(e).__name__}: {e}")

@app.route("/export-pdf")
def export_pdf():
    """Posts + Wahldaten als PDF exportieren."""
    try:
        posts_data    = load_json(DATA_PATH)
        election_data = load_json(ELECTION_PATH)
        pdf_io: BytesIO = build_pdf(posts_data, election_data)
        pdf_io.seek(0)
        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="posts-per-party_all.pdf",
        )
    except Exception as e:
        abort(500, description=f"PDF-Export-Fehler: {type(e).__name__}: {e}")

# ----------------- CSV-DOWNLOADS -----------------
@app.route("/download/posts-csv")
def download_posts_csv():
    """CSV der Posts herunterladen."""
    try:
        return send_file(DATA_CSV_PATH, mimetype="text/csv", as_attachment=True,
                         download_name="posts-per-party_data.csv")
    except FileNotFoundError:
        abort(404, description=f"CSV nicht gefunden: {DATA_CSV_PATH}")
    except Exception as e:
        abort(500, description=f"CSV-Download-Fehler (Posts): {type(e).__name__}: {e}")

@app.route("/download/election-csv")
def download_election_csv():
    """CSV der Wahldaten herunterladen."""
    try:
        return send_file(ELECTION_CSV_PATH, mimetype="text/csv", as_attachment=True,
                         download_name="posts-per-party_election.csv")
    except FileNotFoundError:
        abort(404, description=f"CSV nicht gefunden: {ELECTION_CSV_PATH}")
    except Exception as e:
        abort(500, description=f"CSV-Download-Fehler (Election): {type(e).__name__}: {e}")

# ----------------- SCATTER-PLOT-SPEICHERN -----------------
@app.route("/post-per-party/save-scatter", methods=["POST"])
def save_scatter_image():
    """Speichert ein Scatter-Diagramm, das als base64-Data-URL vom Client kommt.
    - prüft Format, Größe, Base64-Dekodierung
    - speichert als PNG + zusätzlich eine zeitgestempelte Kopie
    """
    try:
        payload = request.get_json(silent=True, force=True) or {}
        data_url = payload.get("imageDataUrl")
        filename = payload.get("filename") or "scatter.png"

        # Validierung (muss .png sein, muss mit data:image/... beginnen)
        if not isinstance(filename, str) or not filename.lower().endswith(".png"):
            filename = "scatter.png"
        if not data_url or not isinstance(data_url, str) or not data_url.startswith("data:image/"):
            abort(400, description="imageDataUrl (data URL) fehlt oder ist ungültig")

        # Base64 extrahieren und dekodieren
        import re, base64
        m = re.match(r"^data:image/[^;]+;base64,(.+)$", data_url)
        if not m:
            abort(400, description="Ungültiges Data-URL-Format")
        img_bytes = base64.b64decode(m.group(1), validate=True)

        # Sicherheitsgrenze: max. 10 MB
        if len(img_bytes) > 10 * 1024 * 1024:
            abort(413, description="Bild zu groß")

        # Speicherung
        out_dir = BASE / "data" / "postPerParty"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        out_path.write_bytes(img_bytes)

        # Kopie mit Zeitstempel
        from datetime import datetime
        ts_name = f"scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        (out_dir / ts_name).write_bytes(img_bytes)

        return jsonify({
            "status": "ok",
            "saved": str(out_path),
            "timestamped": str(out_dir / ts_name)
        })
    except Exception as e:
        code = getattr(e, "code", 500)
        msg = getattr(e, "description", str(e))
        return jsonify({"status": "error", "message": msg}), code

# ----------------- FAVICON -----------------
@app.route("/favicon.png")
@app.route("/favicon.ico")
def favicon():
    """Lädt ein PNG-Favicon (liegt unter templates/favicon.png)."""
    try:
        icon_path = "Sonja/Website/templates/favicon.png"
        return send_file(icon_path, mimetype="image/png")
    except FileNotFoundError:
        abort(404, description="favicon not found")

# ----------------- ERROR HANDLER -----------------
@app.errorhandler(404)
def handle_404(e):
    """Alle 404-Fehler zeigen eine NotFound-Seite mit Beschreibung."""
    return render_template("notFound.html", message=getattr(e, "description", "")), 404

@app.errorhandler(Exception)
def handle_any_error(e):
    """Alle anderen Fehler → NotFound-Seite mit Fehlercode."""
    app.logger.exception("Unerwarteter Fehler")
    code = getattr(e, "code", 500)
    msg = getattr(e, "description", str(e))
    return render_template("notFound.html", message=msg), code

# ----------------- START -----------------
if __name__ == "__main__":
    # Direktstart mit `python app.py`
    app.run(debug=True)
