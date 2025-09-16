from __future__ import annotations

from enum import Enum
from typing import Dict, Any, Optional, List
import json
import requests

API_KEY = "AIzaSyDduHuCkuL2YArj3SKsFXg3TWGSZFWExyQ"
BASE = "https://www.googleapis.com/youtube/v3"

class Party(str, Enum):
    CDU = "CDU"
    CSU = "CSU"
    FDP = "FDP"
    AfD = "AfD"
    SPD = "SPD"
    Gruene = "Gruene"
    Linke = "Linke"
    BSW = "BSW"

# Enum-Keys sind ok, da wir in Python bleiben (kein JSON direkt).
partyJsonWithId = {
    "conservative": {
        Party.CDU: "UCKyWIEse3u7ExKfAWuDMVnw",
        Party.CSU: "UC5AagLvRz7ejBrONZVaA13Q",
        Party.FDP: "UC-sMkrfoQDH-xzMxPNckGFw",
        Party.AfD: "UCq2rogaxLtQFrYG3X3KYNww",
    },
    "progressive": {
        Party.SPD: "UCSmbK1WtpYn2sOGLvSSXkKw",
        Party.Gruene: "UC7TAA2WYlPfb6eDJCeX4u0w",
        Party.Linke: "UCA95T5bSGxNOAODBdbR2rYQ",
        Party.BSW: "UCTCb4Fm41JkTtdwd0CXu4xw",
    },
}

def getId(party: Party) -> Optional[str]:
    """Gibt die Channel-ID für die Partei zurück (oder None)."""
    for family in partyJsonWithId.values():
        cid = family.get(party)
        if cid:
            return cid
    return None

def build_channel_query(party: Party) -> str:
    """Baut die Channels-API-URL für die Partei."""
    channel_id = getId(party)
    if not channel_id:
        raise ValueError(f"Keine Channel-ID für {party.value} gefunden.")
    return f"{BASE}/channels?part=statistics&id={channel_id}&key={API_KEY}"

def fetch_channel_statistics(party: Party) -> Dict[str, Any]:
    """
    Ruft die API mit der von build_channel_query gebauten URL auf
    und gibt ein Dict mit den wichtigsten Kennzahlen zurück.
    """
    url = build_channel_query(party)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"Keine Items für {party.value}: {data}")

    item0 = items[0]
    stats = item0.get("statistics", {})
    channel_id = item0.get("id")

    return {
        "party": party.value,
        # "channel_id": channel_id,
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos_total": int(stats.get("videoCount", 0)),
    }

if __name__ == "__main__":
    all_stats: List[Dict[str, Any]] = []
    for p in Party:
        try:
            all_stats.append(fetch_channel_statistics(p))
        except Exception as e:
            all_stats.append({"party": p.value, "error": str(e)})

    # hübsch ausgeben
    print(json.dumps(all_stats, indent=2, ensure_ascii=False))
