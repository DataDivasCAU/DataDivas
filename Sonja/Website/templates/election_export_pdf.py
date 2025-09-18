# export_pdf.py
from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import pandas as pd
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas

# ---------- Farben & Helfer ----------
PARTY_COLORS = {
    "cdu": "#000000", "csu": "#000000",
    "spd": "#E3000F",
    "fdp": "#FFED00",
    "gruene": "#1AA037", "grüne": "#1AA037",
    "die linke": "#BE3075", "linke": "#BE3075",
    "afd": "#009EE0",
    "bsw": "#00B3A4",
    "sonstige": "#9CA3AF",
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

# ---------- Chart Generation ----------
def create_pie_chart(data, title, filename):
    """Create a pie chart and save it to a BytesIO object."""
    plt.figure(figsize=(6, 4))
    labels = [row["party"] for row in data]
    values = [row["posts"] for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(title)
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_election_pie_chart(data, title, filename):
    """Create a pie chart for election data and save it to a BytesIO object."""
    plt.figure(figsize=(6, 4))
    labels = [row["party"] for row in data]
    values = [row["election"] for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(title)
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_combined_chart(data, title, filename):
    """Create a bar chart with both posts and election data."""
    plt.figure(figsize=(8, 5))
    
    labels = [row["party"] for row in data]
    posts = [row["posts"] for row in data]
    elections = [row["election"] for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    # Scale posts to make them comparable with election percentages
    max_posts = max(posts) if posts else 1
    scaled_posts = [(p / max_posts) * 100 for p in posts]
    
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, scaled_posts, width, label='Posts (skaliert)', color=[c + '80' for c in colors])
    rects2 = ax.bar(x + width/2, elections, width, label='Wahlergebnisse (%)', color=colors)
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Prozent (%)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    
    # Add value labels on top of bars
    def autolabel(rects, original_values=None):
        for i, rect in enumerate(rects):
            height = rect.get_height()
            value = original_values[i] if original_values else height
            ax.annotate(f'{value:.1f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
    
    autolabel(rects1, posts)
    autolabel(rects2)
    
    fig.tight_layout()
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_scatter_chart(data, title):
    """Create a scatter plot for diff posts vs diff election."""
    plt.figure(figsize=(8, 6))
    
    x_values = [row["diffPosts"] for row in data]
    y_values = [row["diffElection"] for row in data]
    labels = [row["party"] for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    plt.figure(figsize=(8, 6))
    
    # Plot points
    for i, label in enumerate(labels):
        plt.scatter(x_values[i], y_values[i], color=colors[i], s=100, label=label)
    
    # Add zero lines
    plt.axhline(y=0, color='#666', linestyle='-', linewidth=2)
    plt.axvline(x=0, color='#666', linestyle='-', linewidth=2)
    
    # Add labels and title
    plt.xlabel('Diff Posts (2025–2021)')
    plt.ylabel('Diff Election (pp)')
    plt.title(title)
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_posts_both_chart(data, title):
    """Create a bar chart for posts from both years."""
    plt.figure(figsize=(10, 6))
    
    labels = [row["party"] for row in data]
    posts2021 = [row.get("posts2021", 0) for row in data]
    posts2025 = [row.get("posts2025", 0) for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, posts2025, width, label='Posts 2025', color=colors)
    rects2 = ax.bar(x + width/2, posts2021, width, label='Posts 2021', color=[c + '80' for c in colors])
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Anzahl Posts')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    
    fig.tight_layout()
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_election_both_chart(data, title):
    """Create a bar chart for election results from both years."""
    plt.figure(figsize=(10, 6))
    
    labels = [row["party"] for row in data]
    election2021 = [row.get("election2021", 0) for row in data]
    election2025 = [row.get("election2025", 0) for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, election2025, width, label='Wahlergebnisse 2025 (%)', color=colors)
    rects2 = ax.bar(x + width/2, election2021, width, label='Wahlergebnisse 2021 (%)', color=[c + '80' for c in colors])
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Prozent (%)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    
    fig.tight_layout()
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

def create_combined_both_chart(data, title):
    """Create a bar chart with both posts and election data for both years."""
    plt.figure(figsize=(12, 8))
    
    labels = [row["party"] for row in data]
    posts2021 = [row.get("posts2021", 0) for row in data]
    posts2025 = [row.get("posts2025", 0) for row in data]
    election2021 = [row.get("election2021", 0) for row in data]
    election2025 = [row.get("election2025", 0) for row in data]
    colors = [_party_color_hex(label) for label in labels]
    
    # Scale posts to make them comparable with election percentages
    max_posts = max(max(posts2021), max(posts2025)) if posts2021 and posts2025 else 1
    scaled_posts2021 = [(p / max_posts) * 100 for p in posts2021]
    scaled_posts2025 = [(p / max_posts) * 100 for p in posts2025]
    
    x = np.arange(len(labels))  # the label locations
    width = 0.2  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create bars
    ax.bar(x - 1.5*width, scaled_posts2025, width, label='Posts 2025 (skaliert)', color=[c + '80' for c in colors])
    ax.bar(x - 0.5*width, scaled_posts2021, width, label='Posts 2021 (skaliert)', color=[c + '60' for c in colors])
    ax.bar(x + 0.5*width, election2025, width, label='Wahlergebnisse 2025 (%)', color=colors)
    ax.bar(x + 1.5*width, election2021, width, label='Wahlergebnisse 2021 (%)', color=[c + '40' for c in colors])
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Prozent (%)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    
    fig.tight_layout()
    
    img_data = BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    plt.close()
    img_data.seek(0)
    return img_data

# ---------- PDF Generation ----------
def create_table_data(data, headers):
    """Convert data to a format suitable for ReportLab Table."""
    table_data = [headers]
    for row in data:
        table_row = []
        for header in headers:
            if header.lower() == 'party' or header.lower() == 'partei':
                table_row.append(row.get('party', ''))
            elif header.lower() == 'posts':
                table_row.append(str(row.get('posts', 0)))
            elif header.lower() == 'election (%)' or header.lower() == 'wahlergebnisse (%)':
                table_row.append(f"{row.get('election', 0):.1f}%")
            elif header.lower() == 'posts 2021':
                table_row.append(str(row.get('posts2021', 0)))
            elif header.lower() == 'posts 2025':
                table_row.append(str(row.get('posts2025', 0)))
            elif header.lower() == 'election 2021 (%)' or header.lower() == 'wahlergebnisse 2021 (%)':
                table_row.append(f"{row.get('election2021', 0):.1f}%")
            elif header.lower() == 'election 2025 (%)' or header.lower() == 'wahlergebnisse 2025 (%)':
                table_row.append(f"{row.get('election2025', 0):.1f}%")
            elif header.lower() == 'diff posts (25-21)':
                diff = row.get('diffPosts', 0)
                table_row.append(f"{'+' if diff > 0 else ''}{diff}")
            elif header.lower() == 'diff election (pp)':
                diff = row.get('diffElection', 0)
                table_row.append(f"{'+' if diff > 0 else ''}{diff:.1f} pp")
            else:
                table_row.append(str(row.get(header.lower(), '')))
        table_data.append(table_row)
    return table_data

# ---------- Hauptfunktion ----------
def build_pdf(posts_data: dict, election_data: dict) -> BytesIO:
    """
    Generate a PDF report with tables and charts.
    
    Args:
        posts_data: Dictionary with post data
        election_data: Dictionary with election data
        
    Returns:
        BytesIO object containing the PDF
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
    first_2021 = _add_election(rows21, e21_map)
    second_2025 = _add_election(rows25, e25_map)

    # Diff-Posts: 2025 - 2021
    _p21 = {r["party"]: r["posts"] for r in first_2021}
    _p25 = {r["party"]: r["posts"] for r in second_2025}
    parties_all = set(_p21) | set(_p25)
    diff_map = {p: _p25.get(p, 0.0) - _p21.get(p, 0.0) for p in parties_all}
    
    # Create data for both years
    both_data = []
    for party in sorted(parties_all):
        both_data.append({
            "party": party,
            "posts2021": _p21.get(party, 0),
            "posts2025": _p25.get(party, 0),
            "election2021": e21_map.get(party, 0),
            "election2025": e25_map.get(party, 0),
            "diffPosts": diff_map.get(party, 0),
            "diffElection": e25_map.get(party, 0) - e21_map.get(party, 0)
        })

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = styles["Title"]
    elements.append(Paragraph("Posts per Party - Datenexport", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # 2025 Data Section
    elements.append(Paragraph("Daten 2025", styles["Heading1"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # 2025 Table
    table_data = create_table_data(second_2025, ["Partei", "Posts", "Election (%)"])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    
    # 2025 Charts
    elements.append(Paragraph("Diagramme 2025", styles["Heading2"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # Create charts for 2025
    posts_pie_2025 = create_pie_chart(second_2025, "1. Posts 2025", "posts_pie_2025")
    election_pie_2025 = create_election_pie_chart(second_2025, "2. Wahlergebnisse 2025", "election_pie_2025")
    combined_chart_2025 = create_combined_chart(second_2025, "3. Posts und Wahlergebnisse 2025", "combined_chart_2025")
    
    # Add charts to PDF
    posts_img_2025 = Image(posts_pie_2025, width=8*cm, height=6*cm)
    election_img_2025 = Image(election_pie_2025, width=8*cm, height=6*cm)
    combined_img_2025 = Image(combined_chart_2025, width=16*cm, height=8*cm)
    
    # Create a table for the charts
    chart_table = Table([
        [posts_img_2025, election_img_2025],
        [Paragraph("1. Diagramm: Nur Posts (2025)", styles["Normal"]), 
         Paragraph("2. Diagramm: Nur Wahlergebnisse (2025)", styles["Normal"])],
        [combined_img_2025, ""],
        [Paragraph("3. Diagramm: Posts und Wahlergebnisse zusammen (2025)", styles["Normal"]), ""]
    ])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 2), (1, 2)),  # Span the combined chart across two columns
        ('SPAN', (0, 3), (1, 3)),  # Span the combined chart label across two columns
    ]))
    elements.append(chart_table)
    elements.append(Spacer(1, 1*cm))
    
    # Page break
    elements.append(Paragraph("", styles["Normal"]))
    elements.append(Spacer(1, 0.5*cm))
    
    # 2021 Data Section
    elements.append(Paragraph("Daten 2021", styles["Heading1"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # 2021 Table
    table_data = create_table_data(first_2021, ["Partei", "Posts", "Election (%)"])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    
    # 2021 Charts
    elements.append(Paragraph("Diagramme 2021", styles["Heading2"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # Create charts for 2021
    posts_pie_2021 = create_pie_chart(first_2021, "1. Posts 2021", "posts_pie_2021")
    election_pie_2021 = create_election_pie_chart(first_2021, "2. Wahlergebnisse 2021", "election_pie_2021")
    combined_chart_2021 = create_combined_chart(first_2021, "3. Posts und Wahlergebnisse 2021", "combined_chart_2021")
    
    # Add charts to PDF
    posts_img_2021 = Image(posts_pie_2021, width=8*cm, height=6*cm)
    election_img_2021 = Image(election_pie_2021, width=8*cm, height=6*cm)
    combined_img_2021 = Image(combined_chart_2021, width=16*cm, height=8*cm)
    
    # Create a table for the charts
    chart_table = Table([
        [posts_img_2021, election_img_2021],
        [Paragraph("1. Diagramm: Nur Posts (2021)", styles["Normal"]), 
         Paragraph("2. Diagramm: Nur Wahlergebnisse (2021)", styles["Normal"])],
        [combined_img_2021, ""],
        [Paragraph("3. Diagramm: Posts und Wahlergebnisse zusammen (2021)", styles["Normal"]), ""]
    ])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 2), (1, 2)),  # Span the combined chart across two columns
        ('SPAN', (0, 3), (1, 3)),  # Span the combined chart label across two columns
    ]))
    elements.append(chart_table)
    elements.append(Spacer(1, 1*cm))
    
    # Page break
    elements.append(Paragraph("", styles["Normal"]))
    elements.append(Spacer(1, 0.5*cm))
    
    # Both Years Data Section
    elements.append(Paragraph("Vergleich 2021 vs 2025", styles["Heading1"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # Both Years Table
    table_data = create_table_data(both_data, [
        "Partei", "Posts 2025", "Election 2025 (%)", 
        "Posts 2021", "Election 2021 (%)", 
        "Diff Posts (25-21)", "Diff Election (pp)"
    ])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    
    # Both Years Charts
    elements.append(Paragraph("Diagramme Vergleich", styles["Heading2"]))
    elements.append(Spacer(1, 0.3*cm))
    
    # Create charts for both years
    posts_both_chart = create_posts_both_chart(both_data, "1. Posts 2021 vs 2025", "posts_both_chart")
    election_both_chart = create_election_both_chart(both_data, "2. Wahlergebnisse 2021 vs 2025", "election_both_chart")
    combined_both_chart = create_combined_both_chart(both_data, "4. Posts und Wahlergebnisse beider Jahre", "combined_both_chart")
    scatter_chart = create_scatter_chart(both_data, "ΔPosts 2025–2021 vs. ΔElection (pp)")
    
    # Add charts to PDF
    posts_both_img = Image(posts_both_chart, width=8*cm, height=6*cm)
    election_both_img = Image(election_both_chart, width=8*cm, height=6*cm)
    combined_both_img = Image(combined_both_chart, width=16*cm, height=8*cm)
    scatter_img = Image(scatter_chart, width=16*cm, height=8*cm)
    
    # Create a table for the charts
    chart_table = Table([
        [posts_both_img, election_both_img],
        [Paragraph("1. Diagramm: Nur Posts", styles["Normal"]), 
         Paragraph("2. Diagramm: Nur Wahlergebnisse", styles["Normal"])],
        [scatter_img, ""],
        [Paragraph("3. Diagramm: ΔPosts 2025–2021 vs. ΔElection (pp)", styles["Normal"]), ""],
        [combined_both_img, ""],
        [Paragraph("4. Diagramm: Posts und Wahlergebnisse beider Jahre", styles["Normal"]), ""]
    ])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 2), (1, 2)),  # Span the scatter chart across two columns
        ('SPAN', (0, 3), (1, 3)),  # Span the scatter chart label across two columns
        ('SPAN', (0, 4), (1, 4)),  # Span the combined chart across two columns
        ('SPAN', (0, 5), (1, 5)),  # Span the combined chart label across two columns
    ]))
    elements.append(chart_table)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer