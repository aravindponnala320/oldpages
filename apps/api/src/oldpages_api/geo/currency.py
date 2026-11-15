"""Which currency a listing is priced in, from the country the book is in.

Keep in sync with apps/web/lib/currency.ts.
"""

from __future__ import annotations

_EURO = ("AT BE CY DE EE ES FI FR GR HR IE IT LT LU LV MT NL PT SI SK").split()

CURRENCY_BY_COUNTRY: dict[str, str] = {
    **{code: "EUR" for code in _EURO},
    "IN": "INR",
    "AE": "AED",
    "AU": "AUD",
    "BD": "BDT",
    "BH": "BHD",
    "BR": "BRL",
    "CA": "CAD",
    "CH": "CHF",
    "CN": "CNY",
    "DK": "DKK",
    "EG": "EGP",
    "GB": "GBP",
    "HK": "HKD",
    "ID": "IDR",
    "IL": "ILS",
    "JP": "JPY",
    "KE": "KES",
    "KR": "KRW",
    "KW": "KWD",
    "LK": "LKR",
    "MV": "MVR",
    "MX": "MXN",
    "MY": "MYR",
    "NG": "NGN",
    "NO": "NOK",
    "NP": "NPR",
    "NZ": "NZD",
    "OM": "OMR",
    "PH": "PHP",
    "PK": "PKR",
    "PL": "PLN",
    "QA": "QAR",
    "SA": "SAR",
    "SE": "SEK",
    "SG": "SGD",
    "TH": "THB",
    "TR": "TRY",
    "TW": "TWD",
    "US": "USD",
    "VN": "VND",
    "ZA": "ZAR",
}

_COUNTRY_NAMES = {"INDIA": "IN"}


def currency_for_country(country: str | None) -> str | None:
    """ISO currency for an ISO country code (or "India"); None when unknown."""
    if not country:
        return None
    code = country.strip().upper()
    code = _COUNTRY_NAMES.get(code, code)
    return CURRENCY_BY_COUNTRY.get(code)
