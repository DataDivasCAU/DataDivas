from __future__ import annotations
from flask import Flask, render_template, jsonify, send_file, abort
from pathlib import Path
from io import BytesIO
import json  
from party import Party, fetch_channel_statistics

# ⬅️ externe Export-Funktion (Datei liegt neben app.py)
from Templates.election_export_xlsx import build_workbook

app = Flask(__name__)

# Pfade stabil relativ zur app.py
BASE = Path(__file__).resolve().parent
DATA_PATH     = "data/data.json"
ELECTION_PATH = "data/election.json"

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

@app.route("/data.json")
def get_data():
    return jsonify(load_json(DATA_PATH))

@app.route("/election.json")
def get_election():
    return jsonify(load_json(ELECTION_PATH))
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


if __name__ == "__main__":
    # App aus dem Ordner starten, in dem app.py liegt:
    #   cd <Ordner-mit-app.py>; python app.py
    app.run(debug=True)
