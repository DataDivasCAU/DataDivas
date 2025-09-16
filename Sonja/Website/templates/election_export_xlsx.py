# export_xlsx.py
from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, NamedStyle
from openpyxl.chart import PieChart, Reference, ScatterChart, Series
from openpyxl.chart.series import DataPoint

# ---------- Farben & Helfer ----------
PARTY_COLORS = {
    "cdu": "000000", "csu": "000000",
    "spd": "E3000F",
    "fdp": "FFED00",
    "gruene": "1AA037", "grüne": "1AA037",
    "die linke": "BE3075", "linke": "BE3075",
    "afd": "009EE0",
    "bsw": "00B3A4",
    "sonstige": "9CA3AF",
}

def _norm(s: str) -> str:
    return str(s).strip().lower()

def _pretty(p: str) -> str:
    m = {
        "gruene": "Grüne", "grüne": "Grüne", "linke": "Linke",
        "cdu": "CDU", "csu": "CSU", "spd": "SPD", "fdp": "FDP",
        "afd": "AfD", "bsw": "BSW"
    }
    return m.get(_norm(p), p)

def _party_color_hex(party: str) -> str:
    k = _norm(party)
    if k in PARTY_COLORS: return PARTY_COLORS[k]
    if "gruen" in k or "grün" in k: return PARTY_COLORS["gruene"]
    if "linke" in k: return PARTY_COLORS["linke"]
    if "cdu" in k or "csu" in k: return PARTY_COLORS["cdu"]
    if "spd" in k: return PARTY_COLORS["spd"]
    if "fdp" in k: return PARTY_COLORS["fdp"]
    if "afd" in k: return PARTY_COLORS["afd"]
    if "bsw" in k: return PARTY_COLORS["bsw"]
    return PARTY_COLORS["sonstige"]

def _contrast_font(hexcolor: str) -> Font:
    c = hexcolor.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    luma = 0.2126*r + 0.7152*g + 0.0722*b
    return Font(color="FFFFFF" if luma < 140 else "000000")

def _color_pie_by_party(pie: PieChart, labels: List[str]) -> None:
    dps: List[DataPoint] = []
    for idx, label in enumerate(labels):
        dp = DataPoint(idx=idx)
        dp.graphicalProperties.solidFill = _party_color_hex(label)
        dps.append(dp)
    if pie.series:
        pie.series[0].data_points = dps

# ---------- Normalisierung ----------
def _rows_from_posts_section(sec: Any) -> List[dict]:
    """Akzeptiert Liste [{party,posts}] oder Dict {party:posts}."""
    rows: List[dict] = []
    if isinstance(sec, list):
        for r in sec:
            p = _pretty(r.get("party", ""))
            rows.append({"party": p, "posts": float(r.get("posts", 0) or 0)})
    elif isinstance(sec, dict):
        for k, v in sec.items():
            rows.append({"party": _pretty(k), "posts": float(v or 0)})
    return rows

def _map_from_election_section(sec: Any) -> Dict[str, float]:
    """Akzeptiert Liste mit einem Dict oder reines Dict; liefert {party: %}."""
    if isinstance(sec, list):
        obj = (sec[0] if sec else {}) or {}
    elif isinstance(sec, dict):
        obj = sec
    else:
        obj = {}
    return {_pretty(k): float(v or 0) for k, v in obj.items()}

def _add_election(rows: List[dict], emap: Dict[str, float]) -> List[dict]:
    parties = {_pretty(r["party"]) for r in rows} | {_pretty(k) for k in emap.keys()}
    out: List[dict] = []
    for p in sorted(parties):
        base = next((x for x in rows if _pretty(x["party"]) == p), {"party": p, "posts": 0})
        out.append({
            "party": p,
            "posts": float(base.get("posts", 0)),
            "election": float(emap.get(p, 0))
        })
    return out

# ---------- Hauptfunktion ----------
def build_workbook(posts_data: dict, election_data: dict) -> BytesIO:
    """
    posts_data versteht:
      - neues Schema:  electionPosts2021 / electionPosts2025
      - altes Schema:  firstElection / secondElection
    election_data: election2021, election2025 (optional diffElection wird nicht benötigt)
    """

    # Posts normalisieren (neues Schema bevorzugt)
    sec21 = posts_data.get("electionPosts2021")
    sec25 = posts_data.get("electionPosts2025")
    if sec21 is None and sec25 is None:
        # Fallback: altes Schema
        sec21 = posts_data.get("firstElection", {})
        sec25 = posts_data.get("secondElection", {})

    rows21 = _rows_from_posts_section(sec21 or {})
    rows25 = _rows_from_posts_section(sec25 or {})

    # Elections (%)
    e21_map = _map_from_election_section(election_data.get("election2021", {}))
    e25_map = _map_from_election_section(election_data.get("election2025", {}))

    # Mergen (für Tabellen)
    first_2021  = _add_election(rows21, e21_map)
    second_2025 = _add_election(rows25, e25_map)

    # Diff-Posts: 2025 - 2021
    _p21 = {r["party"]: r["posts"] for r in first_2021}
    _p25 = {r["party"]: r["posts"] for r in second_2025}
    parties_all = set(_p21) | set(_p25)
    diff_map: Dict[str, float] = {p: _p25.get(p, 0.0) - _p21.get(p, 0.0) for p in parties_all}

    # -------- Excel aufbauen --------
    wb = Workbook()
    header_style = NamedStyle(name="header_style")
    header_style.font = Font(bold=True)
    header_style.alignment = Alignment(vertical="center")
    if "header_style" not in wb.named_styles:
        wb.add_named_style(header_style)

    # ===== Sheet 2021 =====
    ws21 = wb.active
    ws21.title = "2021"
    ws21.append(["Partei", "Posts", "Election (%)"])
    for c in ws21[1]: c.style = header_style
    for r in first_2021:
        ws21.append([r["party"], r["posts"], r["election"]/100.0])
    ws21.column_dimensions["A"].width, ws21.column_dimensions["B"].width, ws21.column_dimensions["C"].width = 18, 12, 16
    for i in range(2, ws21.max_row+1):
        ws21.cell(i,3).number_format = "0.0%"
        bg = _party_color_hex(ws21.cell(i,1).value)
        ws21.cell(i,1).fill = PatternFill("solid", fgColor=bg)
        ws21.cell(i,1).font = _contrast_font(bg)

    pie21 = PieChart()
    pie21.title = "Posts 2021"
    pie21.add_data(Reference(ws21, min_col=2, min_row=1, max_row=ws21.max_row), titles_from_data=True)
    pie21.set_categories(Reference(ws21, min_col=1, min_row=2, max_row=ws21.max_row))
    _color_pie_by_party(pie21, [ws21.cell(r,1).value for r in range(2, ws21.max_row+1)])
    ws21.add_chart(pie21, "E2")

    # ===== Sheet 2025 =====
    ws25 = wb.create_sheet("2025")
    ws25.append(["Partei", "Posts", "Election (%)"])
    for c in ws25[1]: c.style = header_style
    for r in second_2025:
        ws25.append([r["party"], r["posts"], r["election"]/100.0])
    ws25.column_dimensions["A"].width, ws25.column_dimensions["B"].width, ws25.column_dimensions["C"].width = 18, 12, 16
    for i in range(2, ws25.max_row+1):
        ws25.cell(i,3).number_format = "0.0%"
        bg = _party_color_hex(ws25.cell(i,1).value)
        ws25.cell(i,1).fill = PatternFill("solid", fgColor=bg)
        ws25.cell(i,1).font = _contrast_font(bg)

    pie25 = PieChart()
    pie25.title = "Posts 2025"
    pie25.add_data(Reference(ws25, min_col=2, min_row=1, max_row=ws25.max_row), titles_from_data=True)
    pie25.set_categories(Reference(ws25, min_col=1, min_row=2, max_row=ws25.max_row))
    _color_pie_by_party(pie25, [ws25.cell(r,1).value for r in range(2, ws25.max_row+1)])
    ws25.add_chart(pie25, "E2")

    # ===== Sheet Both (mit Scatter) =====
    wsB = wb.create_sheet("Both")
    wsB.append([
        "Partei", "2021 Posts", "2021 Election (%)",
        "2025 Posts", "2025 Election (%)", "Diff Posts (25-21)"
    ])
    for c in wsB[1]: c.style = header_style

    p21_posts = {r["party"]: r["posts"] for r in first_2021}
    p21_elec  = {r["party"]: r["election"] for r in first_2021}
    p25_posts = {r["party"]: r["posts"] for r in second_2025}
    p25_elec  = {r["party"]: r["election"] for r in second_2025}
    parties   = sorted(set(p21_posts)|set(p25_posts)|set(p21_elec)|set(p25_elec)|set(diff_map))

    for p in parties:
        wsB.append([
            p,
            p21_posts.get(p,0.0), (p21_elec.get(p,0.0))/100.0,
            p25_posts.get(p,0.0), (p25_elec.get(p,0.0))/100.0,
            diff_map.get(p,0.0)
        ])

    wsB.column_dimensions["A"].width, wsB.column_dimensions["B"].width = 18, 14
    wsB.column_dimensions["C"].width, wsB.column_dimensions["D"].width, wsB.column_dimensions["E"].width = 18, 14, 20
    wsB.column_dimensions["F"].width = 20
    for i in range(2, wsB.max_row+1):
        wsB.cell(i,3).number_format = "0.0%"
        wsB.cell(i,5).number_format = "0.0%"
        bg = _party_color_hex(wsB.cell(i,1).value)
        wsB.cell(i,1).fill = PatternFill("solid", fgColor=bg)
        wsB.cell(i,1).font = _contrast_font(bg)

    # Scatter: X = Diff Posts (F), Y = 2025 Election (%) (E)
    scatter = ScatterChart()
    scatter.title = "Diff Posts (25-21) vs. 2025 Election (%)"
    scatter.x_axis.title = "Diff Posts (25-21)"
    scatter.y_axis.title = "2025 Election (%)"
    xvalues = Reference(wsB, min_col=6, min_row=2, max_row=wsB.max_row)
    yvalues = Reference(wsB, min_col=5, min_row=2, max_row=wsB.max_row)
    series = Series(yvalues, xvalues, title="Parteien")
    scatter.series.append(series)
    wsB.add_chart(scatter, "H2")

    # Datei zurückgeben
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio
