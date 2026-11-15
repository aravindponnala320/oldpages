"""Offline index of Indian towns and cities (GeoNames, population >= 5000).

Answers city searches instantly without an upstream call, ranks India above
same-named places abroad, and gives every module one canonical spelling per
city ("Bangalore" -> "Bengaluru") so listings, filters and the location
switcher agree with each other.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "in_places.tsv"
_NON_WORD = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Place:
    name: str
    state: str
    latitude: float
    longitude: float
    population: int
    keys: tuple[str, ...]  # normalised name first, then aliases


def normalise(value: str) -> str:
    return _NON_WORD.sub(" ", value.lower()).strip()


@lru_cache(maxsize=1)
def _places() -> tuple[Place, ...]:
    places = []
    for line in _DATA.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, state, lat, lon, population, aliases = line.split("\t")
        keys = tuple(dict.fromkeys(normalise(k) for k in (name, *aliases.split(",")) if k))
        places.append(Place(name, state, float(lat), float(lon), int(population or 0), keys))
    return tuple(places)  # already sorted by population, largest first


@lru_cache(maxsize=1)
def _states() -> dict[str, str]:
    return {normalise(p.state): p.state for p in _places()}


def canonical_state(value: str | None) -> str | None:
    """Return the official spelling of an Indian state/UT, or the input unchanged."""
    if not value:
        return value
    key = normalise(value)
    states = _states()
    if key in states:
        return states[key]
    # Common legacy and short forms seen in postal and OSM data.
    aliases = {
        "orissa": "Odisha",
        "pondicherry": "Puducherry",
        "uttaranchal": "Uttarakhand",
        "nct of delhi": "Delhi",
        "national capital territory of delhi": "Delhi",
        "andaman and nicobar islands": "Andaman and Nicobar",
        "jammu kashmir": "Jammu and Kashmir",
    }
    return aliases.get(key, value)


def _score(place: Place, query: str) -> int:
    """0 = exact name, 1 = exact alias, 2 = name prefix, 3 = alias/word prefix."""
    for index, key in enumerate(place.keys):
        if key == query:
            return 0 if index == 0 else 1
    if place.keys[0].startswith(query):
        return 2
    if any(k.startswith(query) or f" {query}" in f" {k}" for k in place.keys):
        return 3
    return -1


def search(query: str, limit: int = 8) -> list[Place]:
    query = normalise(query)
    if len(query) < 2:
        return []
    matches = [(s, p) for p in _places() if (s := _score(p, query)) >= 0]
    # Stable sort keeps the population order inside each score band.
    matches.sort(key=lambda m: m[0])
    seen: set[tuple[str, str]] = set()
    result = []
    for _, place in matches:
        if (place.name, place.state) in seen:
            continue
        seen.add((place.name, place.state))
        result.append(place)
        if len(result) == limit:
            break
    return result


def find(city: str | None, state: str | None = None) -> Place | None:
    """Exact (name or alias) match for a city, preferring the given state."""
    if not city:
        return None
    key = normalise(city)
    wanted_state = canonical_state(state)
    candidates = [p for p in _places() if key in p.keys]
    if wanted_state:
        in_state = [p for p in candidates if p.state == wanted_state]
        candidates = in_state or candidates
    # Prefer the place whose own name matches over one that merely lists it as an alias.
    candidates.sort(key=lambda p: p.keys[0] != key)
    return candidates[0] if candidates else None


def canonical_city(city: str | None, state: str | None = None) -> str | None:
    place = find(city, state)
    return place.name if place else city


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest(latitude: float, longitude: float, max_km: float = 30.0) -> Place | None:
    """The most significant town near a point: larger places win within their pull radius."""
    best: tuple[float, Place] | None = None
    for place in _places():
        if abs(place.latitude - latitude) > 0.5 or abs(place.longitude - longitude) > 0.5:
            continue
        km = distance_km(latitude, longitude, place.latitude, place.longitude)
        if km > max_km:
            continue
        # A metro pulls from much further away than a small town or a suburb.
        pull = km / max(1.0, math.log10(max(place.population, 10)) - 3) ** 2
        if best is None or pull < best[0]:
            best = (pull, place)
    return best[1] if best else None
