"""One-off extraction of the country profile rows from the UNCTAD 'State of Commodity Dependence 2025' PDF.

Needs the PDF (not stored in the repo, ~8 MB) and the xpdf `pdftotext` binary.  Writes
data/commodity/unctad_scd2025_profiles.csv (all profile pages) and prints the PDF SHA-256.
Usage: python extract_unctad_profiles.py <pdf> [first_page last_page]
commodity_criterion.py reads only the CSV (offline).
"""
import csv, hashlib, re, subprocess, sys
from pathlib import Path

pdf = Path(sys.argv[1])
first, last = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1, 330)
out = Path(__file__).parent / "data" / "commodity" / "unctad_scd2025_profiles.csv"
LAB = "Commodity exports as share of all allocated product exports (percentage)"
UNALLOC = "Unallocated exports as share of merchandise exports (percentage)"
MERCH = "Merchandise exports (millions of dollars)"
NUM = r"(-?[\d,]+\.?\d*|-)"


def vals(text, label):
    m = re.search(re.escape(label) + r"\s+" + NUM + r"\s+" + NUM, text)
    if not m:
        return None, None
    f = lambda s: None if s == "-" else float(s.replace(",", ""))
    return f(m.group(1)), f(m.group(2))


rows = []
for p in range(first, last + 1):
    t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-table", "-enc", "UTF-8", str(pdf), "-"],
                       capture_output=True, text=True, encoding="utf-8").stdout
    if "MERCHANDISE AND COMMODITY EXPORT DEPENDENCE" not in t:
        continue
    name = t.strip().splitlines()[0].strip()
    s1, s2 = vals(t, LAB)
    m1, m2 = vals(t, MERCH)
    u1, u2 = vals(t, UNALLOC)
    rows.append([name, p, s1, s2, m1, m2, u1, u2])
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["country_name_pdf", "pdf_page", "share_2012_2014", "share_2021_2023",
                "merch_exports_musd_2012_2014", "merch_exports_musd_2021_2023",
                "unallocated_share_2012_2014", "unallocated_share_2021_2023"])
    w.writerows(rows)
print(len(rows), "profiles;", "sha256", hashlib.sha256(pdf.read_bytes()).hexdigest())
