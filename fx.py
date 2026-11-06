"""Exchange rates from the European Central Bank, via the free Frankfurter API (JSON, no key needed)."""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import requests
import streamlit as st

CURRENCIES = ["CHF", "EUR", "USD", "GBP"]


@st.cache_data(ttl=6 * 3600)  # the ECB publishes one rate per working day, so asking more often is pointless
def rate_to_chf(currency: str, day: str) -> float:
    """How many CHF one unit of `currency` was worth on `day` (ECB reference rate)."""
    if currency == "CHF":
        return 1.0
    resp = requests.get(f"https://api.frankfurter.dev/v1/{day}",
                        params={"base": currency, "symbols": "CHF"}, timeout=8)
    resp.raise_for_status()  # stop with an error if the API didn't answer properly
    return resp.json()["rates"]["CHF"]


def to_chf(amount: float, currency: str, day: str) -> float:
    return round(amount * rate_to_chf(currency, day), 2)
