#!/usr/bin/env python3
"""Render index.html from site.json and template.html.

Stdlib only. Every fact the page prints lives in site.json; this script
puts it into the template and OBFUSCATES the contact address and the
company's registered details the way Routesmith's public pages do
(templates/_macros.html in the app's repository): the served HTML carries
each word REVERSED, a CSS rule paints it the right way round for a person
with no script, and the small script at the foot of the page un-reverses
the DOM text on load so it copies and reads aloud correctly. No address
regex, and no "at/dot" regex, matches the served bytes.

The SOURCE is protected the same way: this repository is public, so the
address, the company number and the registered office are stored in
site.json REVERSED, under keys ending in `_r` ("ku.oc.…@olleh"), and
un-reversed here on load. A regex over the repository, or GitHub's code
search, meets the same reversed spelling the served page carries.

    python3 build.py                   # write index.html
    python3 build.py --check           # exit 1 if index.html is stale
    python3 build.py --reverse TEXT    # print TEXT reversed, for pasting
                                       # into a `_r` key in site.json

Deterministic: the same site.json and template.html always give the same
index.html, byte for byte (the year comes from site.json, not the clock).
"""

import argparse
import html
import json
import string
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "site.json"
TEMPLATE = HERE / "template.html"
OUTPUT = HERE / "index.html"


def rev(s: str) -> str:
    return s[::-1]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def obf_words(text: str) -> str:
    """The visible half: one span per word, each word reversed.

    Per WORD rather than the whole string, because a whole reversed string
    that wraps paints its lines bottom-up; words in order wrap in order.
    Reverse first, then escape, so an entity is served intact.
    """
    return " ".join(
        f'<span class="obf-w">{esc(rev(word))}</span>' for word in text.split(" ")
    )


def obf_text(value: str) -> str:
    """A fact that must be READABLE without a tap (the registered office)."""
    if not value:
        return ""
    return (
        f'<span class="obf-text" data-nosnippet data-r="{esc(rev(value))}">'
        f"{obf_words(value)}</span>"
    )


def obf_email(address: str) -> str:
    """A mailto link whose address is absent from the DOM until a tap."""
    local, _, domain = address.partition("@")
    if not local or not domain:
        return ""
    spelled = f"{local} at {domain.replace('.', ' dot ')}"
    return (
        f'<a class="obf-mail" href="#" role="link" data-nosnippet '
        f'data-l="{esc(rev(local))}" data-d="{esc(rev(domain))}">'
        f"{obf_words(spelled)}</a>"
    )


def unreverse(cfg: dict) -> dict:
    """Resolve every `<key>_r` (stored reversed) to `<key>` (plain), in
    place, at any depth. A missing `_r` key reads as an empty value."""
    for k in list(cfg.keys()):
        v = cfg[k]
        if isinstance(v, dict):
            unreverse(v)
        elif k.endswith("_r"):
            cfg[k[:-2]] = rev(str(v or ""))
            del cfg[k]
    return cfg


def company_details(company: dict) -> str:
    """The trading disclosures, in the order the app's operator module uses.

    Each part renders only where its value is set; an empty value renders
    nothing rather than a placeholder.
    """
    parts = [company.get("name", "")]
    number = company.get("number", "")
    place = company.get("place", "")
    if number:
        where = f"registered in {place}, " if place else "registered "
        parts.append(f"{where}company number {number}")
    if company.get("office"):
        parts.append(f"registered office {company['office']}")
    if company.get("vat"):
        parts.append(f"VAT number {company['vat']}")
    return obf_text(" · ".join(p for p in parts if p))


def pricing_sentence(pricing: dict) -> str:
    price = pricing.get("premium_price", "")
    if price:
        return (
            f"It costs {esc(price)} a month. The billing period and the way to "
            "change or cancel are shown before you subscribe and on the "
            "subscription page afterwards."
        )
    return (
        "The current price, the billing period and the way to change or "
        "cancel are shown before you subscribe and on the subscription page "
        "afterwards."
    )


def render() -> str:
    cfg = unreverse(json.loads(CONFIG.read_text(encoding="utf-8")))
    company = cfg["company"]
    product = cfg["product"]
    pricing = cfg.get("pricing", {})
    values = {
        "company_name": esc(company["name"]),
        "company_details": company_details(company),
        "email": obf_email(cfg["email"]),
        "site_url": esc(cfg["site_url"]),
        "product_name": esc(product["name"]),
        "product_url": esc(product["url"]),
        "about_url": esc(product["about_url"]),
        "terms_url": esc(product["terms_url"]),
        "privacy_url": esc(product["privacy_url"]),
        "billing": esc(pricing.get("billing", "")),
        "pricing_sentence": pricing_sentence(pricing),
        "year": esc(str(cfg["year"])),
    }
    template = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    return template.substitute(values)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if index.html differs from a fresh render (writes nothing)",
    )
    parser.add_argument(
        "--reverse",
        metavar="TEXT",
        help="print TEXT reversed, the form a `_r` key in site.json holds",
    )
    args = parser.parse_args(argv)
    if args.reverse is not None:
        print(rev(args.reverse))
        return 0
    fresh = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if current != fresh:
            print(f"{OUTPUT.name} is stale: run python3 build.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.name} is current")
        return 0
    OUTPUT.write_text(fresh, encoding="utf-8")
    print(f"wrote {OUTPUT.name} ({len(fresh.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
