import csv
import json
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[3]  # .../DataDivas
QUESTION3_DIR = ROOT / "Diana" / "Question 3"
OUTPUT_DIR = ROOT / "Sonja" / "Website" / "data" / "fridaysForFuture"
OUTPUT_FILE = OUTPUT_DIR / "fridaysForFuture.json"

# Folders to skip
SKIP_FOLDERS = {"RawData", "rawdata"}

# Supported file extensions and their parsers

def read_csv_file(path: Path):
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Try to coerce number-like strings
    for row in rows:
        for k, v in row.items():
            if v is None:
                continue
            vv = v.strip()
            if vv == "":
                row[k] = None
                continue
            # Try int
            try:
                if vv.isdigit() or (vv.startswith("-") and vv[1:].isdigit()):
                    row[k] = int(vv)
                    continue
            except Exception:
                pass
            # Try float
            try:
                row[k] = float(vv)
                continue
            except Exception:
                row[k] = v
    return rows


def collect_folder(folder: Path):
    data = {}
    for file in sorted(folder.iterdir()):
        if file.is_dir():
            # Skip nested dirs by default
            continue
        if file.suffix.lower() == ".csv":
            key = file.stem
            data[key] = read_csv_file(file)
        elif file.suffix.lower() in {".json"}:
            try:
                with file.open(encoding="utf-8") as f:
                    data[file.stem] = json.load(f)
            except Exception:
                # Fallback: store as text if invalid JSON
                data[file.stem] = file.read_text(encoding="utf-8")
        else:
            # For other files (e.g., images), store basic metadata and relative path
            rel = file.relative_to(QUESTION3_DIR)
            data.setdefault("_files", []).append({
                "name": file.name,
                "relative_path": str(rel).replace("\\", "/"),
                "size": file.stat().st_size,
                "suffix": file.suffix,
            })
    return data


def main():
    if not QUESTION3_DIR.exists():
        raise SystemExit(f"Source folder not found: {QUESTION3_DIR}")

    result = {
        "source": str(QUESTION3_DIR),
        "folders": {},
    }

    for sub in sorted(QUESTION3_DIR.iterdir()):
        if not sub.is_dir():
            # Also include top-level non-dir files as metadata
            if sub.suffix.lower() not in {".ipynb"}:
                result.setdefault("_top_level_files", []).append(sub.name)
            continue
        if sub.name in SKIP_FOLDERS:
            continue
        result["folders"][sub.name] = collect_folder(sub)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
