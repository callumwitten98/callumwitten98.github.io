#!/usr/bin/env python3
"""Build the publication list and stats from a SciX (NASA ADS) library.

Run daily by .github/workflows/update-publications.yml. Needs the ADS_TOKEN
environment variable (a SciX/ADS API token). Uses only the Python standard
library, so there is nothing to install.

Writes:
  _includes/publications_generated.html  the stats cards and paper lists
  _data/publications.json                the same information as data
"""

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

# --- Settings you might want to change ---------------------------------------

LIBRARY_ID = "GMHWLZNeQGedFToaW4i9uw"  # the SciX library holding your papers
MY_LAST_NAME = "Witten"
MY_FIRST_INITIAL = "C"
MY_DISPLAY_NAME = "Callum Witten"

API = os.environ.get("ADS_API_URL", "https://api.adsabs.harvard.edu/v1")

JOURNAL_ABBREVIATIONS = {
    "Monthly Notices of the Royal Astronomical Society": "MNRAS",
    "Monthly Notices of the Royal Astronomical Society: Letters": "MNRAS Letters",
    "The Astrophysical Journal": "ApJ",
    "The Astrophysical Journal Letters": "ApJL",
    "The Astrophysical Journal Supplement Series": "ApJS",
    "The Astronomical Journal": "AJ",
    "Astronomy and Astrophysics": "A&A",
    "Astronomy & Astrophysics": "A&A",
    "Nature Astronomy": "Nature Astronomy",
    "The Open Journal of Astrophysics": "OJAp",
    "Publications of the Astronomical Society of Australia": "PASA",
    "Publications of the Astronomical Society of the Pacific": "PASP",
    "Journal of Cosmology and Astroparticle Physics": "JCAP",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_OUT = os.path.join(ROOT, "_includes", "publications_generated.html")
JSON_OUT = os.path.join(ROOT, "_data", "publications.json")

FIELDS = "bibcode,title,author,year,pub,volume,page,identifier,pubnote,comment,citation_count,doctype"


# --- Talking to SciX ---------------------------------------------------------


def api(path, payload=None):
    token = os.environ.get("ADS_TOKEN", "").strip()
    if not token:
        sys.exit("ADS_TOKEN is not set. Add your SciX API token as a repository secret named ADS_TOKEN.")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(API + path, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def fetch_papers():
    query = urllib.parse.urlencode(
        {"q": "docs(library/%s)" % LIBRARY_ID, "fl": FIELDS, "rows": 2000, "sort": "date desc, bibcode desc"}
    )
    return api("/search/query?" + query)["response"]["docs"]


def fetch_metrics(bibcodes):
    return api("/metrics", {"bibcodes": bibcodes, "types": ["indicators", "citations"]})


# --- Formatting --------------------------------------------------------------

ALLOWED_TAGS = re.compile(r"<(/?)(sub|sup|i|em|b|strong)\s*>", re.IGNORECASE)


def clean_title(raw):
    """Escape a title for HTML, keeping simple <sub>/<sup>/<i> markup from SciX."""
    text = html.unescape(raw or "Untitled")
    kept = []

    def stash(match):
        kept.append("<%s%s>" % (match.group(1), match.group(2).lower()))
        return "\x00%d\x00" % (len(kept) - 1)

    text = ALLOWED_TAGS.sub(stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], text)
    return " ".join(text.split())


def split_name(author):
    if "," in author:
        last, given = author.split(",", 1)
        return given.strip(), last.strip()
    parts = author.split()
    return " ".join(parts[:-1]), (parts[-1] if parts else "")


def letters(text):
    return re.sub(r"[^a-z]", "", text.lower())


def is_me(author):
    given, last = split_name(html.unescape(author))
    return letters(last) == letters(MY_LAST_NAME) and letters(given)[:1] == MY_FIRST_INITIAL.lower()


def display_name(author):
    if is_me(author):
        return "<strong>%s</strong>" % html.escape(MY_DISPLAY_NAME)
    given, last = split_name(html.unescape(author))
    return html.escape(("%s %s" % (given, last)).strip(), quote=False)


def format_authors(authors):
    """First few authors, then '& others' (naming me if I'm further down the list)."""
    if not authors:
        return ""
    my_position = next((i for i, a in enumerate(authors) if is_me(a)), None)
    shown = 3 if (my_position is not None and my_position < 3) else 2
    names = [display_name(a) for a in authors[:shown]]
    text = ", ".join(names)
    if len(authors) > shown:
        if my_position is not None and my_position >= shown:
            text += " &amp; others including <strong>%s</strong>" % html.escape(MY_DISPLAY_NAME)
        else:
            text += " &amp; others"
    return text


SUBMITTED = re.compile(r"\b((?:submitted|accepted(?: for publication)?)\s+(?:to|in|by|for)\s+[^.;,()]+)", re.IGNORECASE)


def format_venue(paper):
    pub = (paper.get("pub") or "").strip()
    if not pub or "arxiv" in pub.lower():
        notes = html.unescape(" ".join((paper.get("pubnote") or []) + (paper.get("comment") or [])))
        match = SUBMITTED.search(notes)
        if match:
            phrase = " ".join(match.group(1).split())
            return html.escape(phrase[0].upper() + phrase[1:])
        return "Preprint"
    venue = JOURNAL_ABBREVIATIONS.get(pub, pub)
    volume = (paper.get("volume") or "").strip()
    page = paper.get("page") or []
    page = (page[0] if isinstance(page, list) and page else page or "").strip()
    if volume:
        venue += " " + volume
        if page:
            venue += ", " + page
    return html.escape(venue)


def arxiv_id(paper):
    for ident in paper.get("identifier") or []:
        match = re.match(r"(?:arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?$", ident)
        if match:
            return match.group(1)
    return None


def build_entry(paper):
    bibcode = paper["bibcode"]
    arxiv = arxiv_id(paper)
    return {
        "year": paper.get("year") or "",
        "title": clean_title((paper.get("title") or ["Untitled"])[0]),
        "authors": format_authors(paper.get("author") or []),
        "venue": format_venue(paper),
        "bibcode": bibcode,
        "ads_url": "https://ui.adsabs.harvard.edu/abs/%s/abstract" % urllib.parse.quote(bibcode, safe=""),
        "arxiv_id": arxiv,
        "arxiv_url": ("https://arxiv.org/abs/%s" % arxiv) if arxiv else None,
        "citations": paper.get("citation_count") or 0,
    }


def render_list(title, entries):
    if not entries:
        return ""
    items = []
    for e in entries:
        links = ""
        if e["arxiv_url"]:
            links = ' <a href="%s">arXiv:%s</a>' % (e["arxiv_url"], e["arxiv_id"])
        items.append(
            '  <li><span class="pub-year">%s</span> <a class="pub-title" href="%s">%s</a>.'
            ' <span class="pub-authors">%s</span>, <span class="pub-venue">%s</span>.%s</li>'
            % (e["year"], e["ads_url"], e["title"], e["authors"], e["venue"], links)
        )
    return '<h2 class="pub-section">%s <span class="pub-count">%d</span></h2>\n<ul class="pub-list">\n%s\n</ul>\n' % (
        title,
        len(entries),
        "\n".join(items),
    )


def render(stats, groups):
    cards = [
        ("Papers", stats["papers"]),
        ("First-author", stats["first_author"]),
        ("Citations", stats["citations"]),
        ("h-index", stats["h_index"]),
    ]
    out = ["<!-- Generated by bin/update_publications.py from SciX. Do not edit by hand: it is overwritten daily. -->"]
    out.append('<section class="pub-stats" aria-label="Publication metrics">')
    for label, value in cards:
        out.append(
            '  <div class="pub-stat"><p class="pub-stat-label">%s</p><p class="pub-stat-value">%s</p></div>' % (label, value)
        )
    out.append("</section>")
    out.append(render_list("First-author papers", groups["first_author"]))
    out.append(render_list("Second-author papers", groups["second_author"]))
    out.append(render_list("Co-authored papers", groups["co_authored"]))
    # {% raw %} stops Jekyll from treating any braces in paper titles as template code.
    return "{% raw %}\n" + "\n".join(part for part in out if part) + "{% endraw %}\n"


def main():
    papers = fetch_papers()
    if not papers:
        sys.exit("The SciX library returned no papers; leaving the current list unchanged.")

    groups = {"first_author": [], "second_author": [], "co_authored": []}
    for paper in papers:
        authors = paper.get("author") or []
        position = next((i for i, a in enumerate(authors) if is_me(a)), None)
        key = "first_author" if position == 0 else "second_author" if position == 1 else "co_authored"
        groups[key].append(build_entry(paper))

    metrics = fetch_metrics([p["bibcode"] for p in papers])
    stats = {
        "papers": len(papers),
        "first_author": len(groups["first_author"]),
        "citations": int(metrics["citation stats"]["total number of citations"]),
        "h_index": int(metrics["indicators"]["h"]),
    }

    os.makedirs(os.path.dirname(HTML_OUT), exist_ok=True)
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(render(stats, groups))
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, **groups}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Papers: %(papers)d  first-author: %(first_author)d  citations: %(citations)d  h-index: %(h_index)d" % stats)


if __name__ == "__main__":
    main()
