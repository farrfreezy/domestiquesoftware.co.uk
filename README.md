# domestiquesoftware.co.uk

The public website of Domestique Software Ltd, the company that runs
[Routesmith](https://app.routesmith.cc/). One static page, hosted on GitHub
Pages, with no build step on the host, no web fonts, no scripts beyond the
one that un-reverses the obfuscated contact details, and nothing fetched from
anywhere else.

It exists so that a payment provider, a customer or a registrar can find, on
a plain public page, what the law and Stripe's account activation both ask
for:

| Needed | Where on the page |
|---|---|
| Legal name of the business | title, intro, footer, Company details |
| What is sold | What we make |
| Pricing and billing period | Plans and pricing |
| Cancellation and refund policy | Cancellation and refunds |
| Terms of service | Terms and privacy (links to Routesmith's public terms) |
| Privacy policy | Terms and privacy (links to Routesmith's public notice) |
| Contact details | Contact |
| Registered name, number, place of registration, registered office (Companies Act 2006 s.82 and the Trading Disclosures Regulations) | Company details |

## Files

| File | What it is |
|---|---|
| `site.json` | Every fact the page prints: company details, contact address, product links, pricing copy, the copyright year. **Edit this, not `index.html`.** The email, company number and registered office are stored REVERSED under keys ending in `_r` (see below). |
| `template.html` | The page, with `$placeholders` for the values above. |
| `build.py` | Renders `template.html` + `site.json` → `index.html` (Python 3, standard library only). |
| `index.html` | **Generated.** Committed so GitHub Pages serves it directly. |
| `style.css` | The stylesheet. |
| `CNAME` | The custom domain, which GitHub Pages reads. Keep it. |
| `.nojekyll` | Tells Pages to serve the files as they are. |

## Editing

1. Change `site.json` (or, for copy, `template.html`).
2. Run `python3 build.py`.
3. Commit `index.html` together with the change. `python3 build.py --check`
   exits 1 if `index.html` is stale, so run it before committing.

The output is deterministic: the same inputs always give the same bytes.

Empty values render nothing, never a placeholder. Two are empty on purpose
until they exist:

- `company.vat_r` — the VAT number, once registered (reversed, like the other `_r` keys).
- `pricing.premium_price` — the Premium price (for example `£4`); until it is
  set, the page says the price is shown before you subscribe.

## How the contact details are protected from scraping

This repository is public (free GitHub Pages needs that), so the same rule
applies to the source as to the page: `site.json` holds the email, the
company number and the registered office **reversed**, under keys ending
in `_r`, and `build.py` un-reverses them when it renders. GitHub's code
search and any regex over the repository meet the same reversed spelling
the served page carries. To change one of them:

```bash
python3 build.py --reverse "new.address@domestiquesoftware.co.uk"
# paste the printed value into the matching `_r` key, then rebuild
```


The email address and the registered details are obfuscated the way
Routesmith's own public pages do it, and `build.py` applies it so nobody
hand-reverses a string:

- The served HTML carries each **word reversed** (`olleh ta …`), and the
  whole value reversed in a `data-` attribute. No email regex, no "at/dot"
  regex and no postcode regex matches the served bytes.
- A CSS rule (`.obf-w { unicode-bidi: isolate-override; direction: rtl }`)
  paints each word the right way round, so a person with JavaScript off
  still reads it correctly.
- The script at the foot of `index.html` un-reverses the DOM text on load, so
  it copies and reads aloud correctly, and builds the `mailto:` link only when
  someone reaches for it (`pointerdown` / `focus`).
- `data-nosnippet` asks Google to keep the values out of search snippets, and
  the JSON-LD names only the company and the site, never an address or
  number (structured data is the one copy a harvester reads with no regex).

What it does **not** do: hide the details from a crawler that renders the
page, or from the public Companies House register, which publishes the
registered office anyway. A crawler that does *not* render sees reversed
words. Stripe's reviewers use a browser, where the page reads correctly with
or without JavaScript; if an automated check ever reports "no contact
details", the address can be printed plain for the duration of the review
(replace `$email` in `template.html` with the address, rebuild) and
re-obfuscated after.

## Hosting on GitHub Pages

This repository is the site: `index.html` at the root is what Pages serves.

1. The repository must be public for Pages to be free (Pages on a private
   repository needs a paid plan).
2. Repository **Settings → Pages**: Source *Deploy from a branch*, branch
   `main`, folder `/ (root)`. Custom domain `domestiquesoftware.co.uk` (the
   `CNAME` file keeps it set across pushes). Once the DNS below has
   propagated and the certificate has issued, tick **Enforce HTTPS**.
3. DNS at the registrar or zone host, for the apex `domestiquesoftware.co.uk`:

   | Type | Name | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `<github-user>.github.io` |

   If the zone is on Cloudflare, leave these records **DNS only** (grey
   cloud) until Pages has verified the domain and issued its certificate;
   proxying them first makes the verification and the HTTPS enforcement
   check fail. GitHub's own instructions:
   <https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site>.

4. Optionally verify the domain for the account under **Settings → Pages**
   (a `_github-pages-challenge-<user>` TXT record), which stops anyone else
   claiming it on Pages.

Nothing else is needed: no Actions workflow, no build on the host.

## Checking it locally

```bash
python3 build.py --check
python3 -m http.server 8000     # then open http://localhost:8000/
```
