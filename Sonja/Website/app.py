from __future__ import annotations
from flask import Flask, render_template, jsonify, send_file, abort
from pathlib import Path
from io import BytesIO
import json  
from party import Party, fetch_channel_statistics

# ⬅️ externe Export-Funktionen (Dateien liegen neben app.py)
from templates.election_export_xlsx import build_workbook
from templates.election_export_pdf import build_pdf

app = Flask(__name__)

# Pfade stabil relativ zur app.py
BASE = Path(__file__).resolve().parent
DATA_PATH     = "data/postPerParty/data.json"
ELECTION_PATH = "data/postPerParty/election.json"

def load_json(path: str):
    """Hilfsfunktion: JSON-Datei laden und als Python-Dict zurückgeben."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        abort(404, description=f"Datei nicht gefunden: {path}")
    except json.JSONDecodeError as e:
        abort(500, description=f"JSON-Fehler in {path}: {e}")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/post-per-party")
def post_per_party():
    return render_template("post-per-party.html")

@app.route("/antivax-yt")
def antivax():
    return render_template("antivax.html")

@app.route("/afd")
def afd():
    return render_template("afd.html")

@app.route("/fridaysForFuture")
def fridaysForFuture():
    return render_template("fridaysForFuture.html")

@app.route("/meToo")
def meToo():
    return render_template("meToo.html")

@app.route("/wagenknecht")
def wagenknecht():
    return render_template("wagenknecht.html")

@app.route("/tradwife")
def tradwife():
    return render_template("tradwife.html")

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

@app.route("/kontakt")
def kontakt():
    return render_template("kontakt.html")

@app.route("/data.json")
def get_data():
    return jsonify(load_json(DATA_PATH))

@app.route("/election.json")
def get_election():
    return jsonify(load_json(ELECTION_PATH))

@app.route("/answer_seven.json")
def get_answer_seven():
    answer_seven_path = Path(BASE) / "data" / "tradewife" / "answer_seven.json"
    return jsonify(load_json(str(answer_seven_path)))
@app.route("/load_yt_current_data_of_parties")
def channel_stats_all():
    results = []
    for party in Party:
        try:
            stats = fetch_channel_statistics(party)
            results.append(stats)
        except Exception as e:
            results.append({
                "party": party.value,
                "error": str(e)
            })
    return jsonify(results)


@app.route("/export-excel")
def export_excel():
    try:
        posts_data    = load_json(DATA_PATH)      # <- dict
        election_data = load_json(ELECTION_PATH)  # <- dict
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
    try:
        posts_data    = load_json(DATA_PATH)      # <- dict
        election_data = load_json(ELECTION_PATH)  # <- dict
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

# ----------------- ERROR HANDLER -----------------

@app.errorhandler(404)
def handle_404(e):
    # Alle unbekannten URLs → notFound.html
    return render_template("notFound.html", message=getattr(e, "description", "")), 404

@app.errorhandler(Exception)
def handle_any_error(e):
    # ALLE anderen Fehler → 500 (oder Fehlercode, falls vorhanden) + notFound.html
    app.logger.exception("Unerwarteter Fehler")
    code = getattr(e, "code", 500)
    msg = getattr(e, "description", str(e))
    return render_template("notFound.html", message=msg), code

if __name__ == "__main__":
    # App aus dem Ordner starten, in dem app.py liegt:
    #   cd <Ordner-mit-app.py>; python app.py
    app.run(debug=True)
