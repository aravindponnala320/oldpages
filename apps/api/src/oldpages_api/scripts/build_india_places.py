"""Rebuild geo/data/in_places.tsv from GeoNames (CC BY 4.0, https://www.geonames.org).

    curl -O https://download.geonames.org/export/dump/cities5000.zip && unzip cities5000.zip
    curl -O https://download.geonames.org/export/dump/admin1CodesASCII.txt
    python -m oldpages_api.scripts.build_india_places cities5000.txt admin1CodesASCII.txt

Output columns: name, state, latitude, longitude, population, comma-separated aliases.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "geo" / "data" / "in_places.tsv"
_ASCII_NAME = re.compile(r"^[A-Z][A-Za-z .'-]{2,39}$")
MAX_ALIASES = 12

# Everyday names that must survive the MAX_ALIASES cut.
EXTRA_ALIASES = {
    ("Visakhapatnam", "Andhra Pradesh"): ("Vizag",),
    ("Thiruvananthapuram", "Kerala"): ("Trivandrum",),
    ("Bengaluru", "Karnataka"): ("Bangalore",),
    ("Gurugram", "Haryana"): ("Gurgaon",),
    ("Prayagraj", "Uttar Pradesh"): ("Allahabad",),
}

# Sub-districts GeoNames lists as towns; they would shadow the real city nearby.
SKIP = {("Kanayannur", "Kerala")}  # taluk around Kochi


def main(cities_path: str, admin1_path: str) -> None:
    states = {}
    for line in Path(admin1_path).read_text(encoding="utf-8").splitlines():
        code, name, *_ = line.split("\t")
        if code.startswith("IN."):
            states[code[3:]] = name
    rows = []
    for line in Path(cities_path).read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if f[8] != "IN" or f[7] in {"PPLQ", "PPLH", "PPLW"}:
            continue
        # asciiname: "Dharavi" rather than "Dhārāvi".
        name, state = f[2], states.get(f[10])
        if not state or (name, state) in SKIP:
            continue
        aliases: list[str] = []
        for alias in (*EXTRA_ALIASES.get((name, state), ()), *f[3].split(",")):
            alias = alias.strip()
            if (
                _ASCII_NAME.match(alias)
                and alias.lower() != name.lower()
                and alias.lower() not in {a.lower() for a in aliases}
            ):
                aliases.append(alias)
        rows.append((name, state, f[4], f[5], f[14], ",".join(aliases[:MAX_ALIASES])))
    rows.sort(key=lambda r: -int(r[4] or 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write("# Indian places from GeoNames (CC BY 4.0). Rebuild: build_india_places.py\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")
    print(f"wrote {len(rows)} places to {OUT}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
