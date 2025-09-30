from __future__ import annotations
from flask import Flask, render_template, jsonify, send_file, abort, request
from pathlib import Path
from io import BytesIO
import json  
from party import Party, fetch_channel_statistics

app = Flask(__name__)
# Preserve insertion order of keys in JSON responses (disable Flask default sorting)
app.json.sort_keys = False

#collection of paths
BASE = Path(__file__).resolve().parent
DATA_PATH       = "data/postPerParty/data.json"
ELECTION_PATH   = "data/postPerParty/election.json"
DATA_CSV_PATH   = BASE / "data" / "postPerParty" / "data.csv"
ELECTION_CSV_PATH = BASE / "data" / "postPerParty" / "election.csv"
FRIDAYS_JSON_PATH = BASE / "data" / "fridaysForFuture" / "fridaysForFuture.json"
FFF_STRIKES_CSV_PATH = BASE / "data" / "fridaysForFuture" / "fff_germany_strikes.csv"
AFD_COMBINED_JSON_PATH = BASE / "data" / "afd" / "AfD_combined_relative.json"
AFD_DAILY_JSON_PATH = BASE / "data" / "afd" / "AfD_combined_daily_relative.json"

def load_json(path: str):
    """Helper function: Load JSON file and return it as a Python dict."""
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

@app.route("/post-per-party/stats")
def post_per_party_stats():
    # Renders a page that shows current party channel stats with table and chart
    return render_template("stats.html")

@app.route("/antivax-yt")
def antivax():
    return render_template("antivax.html")

# Antivax data endpoint (like tradwife pattern): serves the antivax answer_one.json
@app.route("/answer_one.json")
def antivax_answer_one():
    path = Path(BASE) / "data" / "antivax" / "answer_one.json"
    return jsonify(load_json(str(path)))

@app.route("/afd")
def afd():
    return render_template("afd.html")

@app.route("/fridaysForFuture")
def fridaysForFuture():
    return render_template("fridaysForFuture.html")

@app.route("/fridaysForFuture.json")
def fridaysForFuture_json():
    return jsonify(load_json(str(FRIDAYS_JSON_PATH)))

@app.route("/fff_strikes.json")
def fff_strikes_json():
    """Reads the CSV file containing strike data and returns a list of date strings (YYYY-MM-DD)."""
    try:
        if not FFF_STRIKES_CSV_PATH.exists():
            abort(404, description=f"CSV nicht gefunden: {FFF_STRIKES_CSV_PATH}")
        lines = FFF_STRIKES_CSV_PATH.read_text(encoding="utf-8").splitlines()
        # Skip header and empties, trim spaces
        dates = [ln.strip() for ln in lines[1:] if ln and ln.strip()]
        # Basic validation: keep only yyyy-mm-dd pattern
        import re
        pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        dates = [d for d in dates if pat.match(d)]
        return jsonify(dates)
    except Exception as e:
        abort(500, description=f"Fehler beim Lesen der Streik-CSV: {type(e).__name__}: {e}")

@app.route("/afd_combined.json")
def afd_combined_json():
    return jsonify(load_json(str(AFD_COMBINED_JSON_PATH)))

@app.route("/afd_daily.json")
def afd_daily_json():
    return jsonify(load_json(str(AFD_DAILY_JSON_PATH)))

# AfD: expose individual datasets (weekly and daily)
@app.route("/afd_wiki.json")
def afd_wiki_json():
    path = Path(BASE) / "data" / "afd" / "afd_wiki.json"
    return jsonify(load_json(str(path)))

@app.route("/afd_yt.json")
def afd_yt_json():
    path = Path(BASE) / "data" / "afd" / "afd_yt.json"
    return jsonify(load_json(str(path)))

@app.route("/afd_wiki_daily.json")
def afd_wiki_daily_json():
    path = Path(BASE) / "data" / "afd" / "afd_wiki_daily.json"
    return jsonify(load_json(str(path)))

@app.route("/afd_yt_daily.json")
def afd_yt_daily_json():
    path = Path(BASE) / "data" / "afd" / "afd_yt_daily.json"
    return jsonify(load_json(str(path)))

@app.route("/meToo")
def meToo():
    return render_template("meToo.html")

@app.route("/wagenknecht")
def wagenknecht():
    return render_template("wagenknecht.html")

@app.route("/wagenknecht_words_a.json")
def wagenknecht_words_a():
    path = Path(BASE) / "data" / "wagenknecht" / "Sahra_Wagenknecht_Words_A.json"
    return jsonify(load_json(str(path)))

@app.route("/wagenknecht_words_b.json")
def wagenknecht_words_b():
    path = Path(BASE) / "data" / "wagenknecht" / "Sahra_Wagenknecht_Words_B.json"
    return jsonify(load_json(str(path)))

@app.route("/wagenknecht_words_combined.json")
def wagenknecht_words_combined():
    """Sums the frequencies from A and B per word and returns a combined list.
    Output format: [{“words”: <word>, “numbers”: <sum>}, ...] sorted by numbers desc.
    """
    path_a = Path(BASE) / "data" / "wagenknecht" / "Sahra_Wagenknecht_Words_A.json"
    path_b = Path(BASE) / "data" / "wagenknecht" / "Sahra_Wagenknecht_Words_B.json"
    try:
        data_a = load_json(str(path_a)) or []
        data_b = load_json(str(path_b)) or []
        freq = {}
        # beide listen zusammenführen und zählen (case-insensitive)
        for entry in [*(data_a or []), *(data_b or [])]:
            w = str(entry.get("words", "")).strip()
            if not w:
                continue
            key = w.lower()
            n = int(entry.get("numbers", 0) or 0)
            freq[key] = freq.get(key, 0) + n
        combined = [{"words": w, "numbers": c} for w, c in freq.items()]
        combined.sort(key=lambda x: x["numbers"], reverse=True)
        return jsonify(combined)
    except Exception as e:
        abort(500, description=f"Fehler beim Kombinieren der Wagenknecht-Wortlisten: {type(e).__name__}: {e}")

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

@app.route("/hype_sentiment.json")
def get_hype_sentiment():
    hype_sentiment_path = Path(BASE) / "data" / "hypeSentiment" / "sentiment.json"
    return jsonify(load_json(str(hype_sentiment_path)))

@app.route("/meToo_timeseries.json")
def get_meToo_timeseries():
    meToo_series_path = Path(BASE) / "data" / "meToo" / "meToo.json"
    return jsonify(load_json(str(meToo_series_path)))

@app.route("/meToo_sentiment.json")
def get_meToo_sentiment():
    meToo_sentiment_path = Path(BASE) / "data" / "meToo" / "sentiment.json"
    return jsonify(load_json(str(meToo_sentiment_path)))

@app.route("/load_yt_current_data_of_parties")
def channel_stats_all():
    from datetime import datetime
    # Fetch current stats for all parties; add timestamp; persist to stats.json
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for party in Party:
        try:
            stats = fetch_channel_statistics(party)
            # Ensure structure and add timestamp
            stats["timestamp"] = timestamp
            results.append(stats)
        except Exception as e:
            # If quota or any error: return an error status but still include timestamp
            results.append({
                "party": party.value,
                "error": "konnte nicht geladen werden",
                "details": str(e),
                "timestamp": timestamp
            })
    # Persist latest request as JSON under data/postPerParty/stats.json
    try:
        stats_path = BASE / "data" / "postPerParty" / "stats.json"
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception:
        # Do not fail API if saving to disk fails
        pass
    return jsonify(results)

@app.route("/export-current-stats.json")
def export_current_stats_json():
    """Erzeugt die aktuellen YouTube-Statistiken aller Parteien und gibt sie als JSON-Download zurück."""
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
    # send_file is nicer for filenames, but jsonify is fine; set headers for download behavior
    resp = jsonify(results)
    resp.headers["Content-Disposition"] = "attachment; filename=current_party_stats.json"
    return resp


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

# -------- CSV DOWNLOADS (verwenden lokale CSV-Dateien) --------
@app.route("/download/posts-csv")
def download_posts_csv():
    try:
        return send_file(
            DATA_CSV_PATH,
            mimetype="text/csv",
            as_attachment=True,
            download_name="posts-per-party_data.csv",
        )
    except FileNotFoundError:
        abort(404, description=f"CSV nicht gefunden: {DATA_CSV_PATH}")
    except Exception as e:
        abort(500, description=f"CSV-Download-Fehler (Posts): {type(e).__name__}: {e}")

@app.route("/download/election-csv")
def download_election_csv():
    try:
        return send_file(
            ELECTION_CSV_PATH,
            mimetype="text/csv",
            as_attachment=True,
            download_name="posts-per-party_election.csv",
        )
    except FileNotFoundError:
        abort(404, description=f"CSV nicht gefunden: {ELECTION_CSV_PATH}")
    except Exception as e:
        abort(500, description=f"CSV-Download-Fehler (Election): {type(e).__name__}: {e}")

# -------- Save scatter image from Post-per-Party page --------
@app.route("/post-per-party/save-scatter", methods=["POST"])
def save_scatter_image():
    """Accepts a JSON payload with a data URL of the scatter chart and saves it as PNG under data/postPerParty.
    Expected JSON: { "imageDataUrl": "data:image/png;base64,....", "filename": "optional.png" }
    Returns JSON with status and saved path.
    """
    try:
        payload = request.get_json(silent=True, force=True) or {}
        data_url = payload.get("imageDataUrl")
        filename = payload.get("filename") or "scatter.png"
        if not isinstance(filename, str) or not filename.lower().endswith(".png"):
            filename = "scatter.png"
        if not data_url or not isinstance(data_url, str) or not data_url.startswith("data:image/"):
            abort(400, description="imageDataUrl (data URL) fehlt oder ist ungültig")
        # Extract base64 part
        import re, base64
        m = re.match(r"^data:image/[^;]+;base64,(.+)$", data_url)
        if not m:
            abort(400, description="Ungültiges Data-URL-Format")
        b64 = m.group(1)
        try:
            img_bytes = base64.b64decode(b64, validate=True)
        except Exception:
            abort(400, description="Base64-Dekodierung fehlgeschlagen")
        # Basic size guard (<= 10 MB)
        if len(img_bytes) > 10 * 1024 * 1024:
            abort(413, description="Bild zu groß")
        # Save under data/postPerParty
        out_dir = BASE / "data" / "postPerParty"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        # Also save a timestamped copy for history
        from datetime import datetime
        ts_name = f"scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(out_dir / ts_name, "wb") as f:
            f.write(img_bytes)
        return jsonify({
            "status": "ok",
            "saved": str(out_path),
            "timestamped": str(out_dir / ts_name)
        })
    except Exception as e:
        code = getattr(e, "code", 500)
        msg = getattr(e, "description", str(e))
        return jsonify({"status": "error", "message": msg}), code

# -------- FAVICON ROUTES --------
@app.route("/favicon.png")
@app.route("/favicon.ico")
def favicon():
    """Serve the favicon from the templates folder as PNG."""
    try:
        icon_path = "Sonja/Website/templates/favicon.png"
        return send_file(icon_path, mimetype="image/png")
    except FileNotFoundError:
        abort(404, description="favicon not found")

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
