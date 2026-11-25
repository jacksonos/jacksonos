"""Render cards/*.svg from data/contributions.json + assets/portrait.txt + fonts/*.woff.

data/contributions.json = GitHub GraphQL `contributionsCollection.contributionCalendar`:
  {"totalContributions": int, "weeks": [{"contributionDays": [{"date": "YYYY-MM-DD", "contributionCount": int}]}]}
Env STATIC=1 -> no animations (final state), used for screenshots.
Stdlib only.
"""
import base64
import json
import os
import textwrap
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ANIM = not os.environ.get("STATIC")
C = {"paper": "#FAFAF7", "ink": "#111111", "grey": "#6B6B66", "line": "#E6E4DD", "accent": "#FF6A1A"}
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, Consolas, monospace"
FONTS = {  # key -> (family, weight, file)
    "serif": ("Instrument Serif", 400, "instrument-serif-400-normal.woff"),
    "sans": ("Geist", 400, "geist-sans-400-normal.woff"),
    "sans500": ("Geist", 500, "geist-sans-500-normal.woff"),
    "mono": ("Geist Mono", 400, "geist-mono-400-normal.woff"),
}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
MONO_ADV = 0.6  # Geist Mono advance width in em

CSS = f"text{{font-family:{SANS}}}.serif{{font-family:{SERIF}}}.mono{{font-family:{MONO}}}"
ANIM_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:translateY(32px)}60%{opacity:1;transform:translateY(-7px)}100%{opacity:1;transform:none}}
@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-3px)}}
@keyframes pulse{0%{transform:scale(1);opacity:.5}100%{transform:scale(3);opacity:0}}
@keyframes draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}
.fade{animation:fade .5s ease-out both}
.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.tile{animation:pop .9s cubic-bezier(.2,.7,.2,1) both}
.arrow{animation:nudge 2.4s ease-in-out 1.8s infinite}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}
.uline{transform-box:fill-box;transform-origin:left;animation:draw .7s ease-out both}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.sheen{display:none}}
"""


def dl(s):
    """inline animation-delay (empty in STATIC mode)"""
    return f' style="animation-delay:{s:.3f}s"' if ANIM else ""


def font_css(keys):
    out = ""
    for k in keys:
        fam, wt, f = FONTS[k]
        b64 = base64.b64encode((ROOT / "fonts" / f).read_bytes()).decode()
        out += f"@font-face{{font-family:'{fam}';font-weight:{wt};src:url(data:font/woff;base64,{b64}) format('woff')}}"
    return out


def svg(w, h, title, desc, body, fonts, defs=""):
    css = font_css(fonts) + CSS + (ANIM_CSS if ANIM else "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
        f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>"
        f"<style>{css}</style>{defs}"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{C["paper"]}" stroke="{C["line"]}"/>'
        f"{body}</svg>\n"
    )


def stats(path):
    cal = json.loads(path.read_text(encoding="utf-8"))
    days = sorted(
        (date.fromisoformat(d["date"]), d["contributionCount"])
        for wk in cal["weeks"] for d in wk["contributionDays"]
    )
    counts = dict(days)
    last = days[-1][0]
    # last 12 calendar months ending at the last day's month
    ym = [(last.year * 12 + last.month - 1) - i for i in range(11, -1, -1)]
    by_month = Counter()
    for d, n in days:
        by_month[d.year * 12 + d.month - 1] += n
    months = [(m % 12, by_month[m]) for m in ym]
    # streak: today may still be empty without breaking it
    d = last if counts[last] else last - timedelta(days=1)
    streak = 0
    while counts.get(d, 0) > 0:
        streak += 1
        d -= timedelta(days=1)
    return {
        "cal": cal, "days": days, "total": cal["totalContributions"], "months": months,
        "streak": streak, "active": sum(1 for _, n in days if n),
        "busiest": max(days, key=lambda x: (x[1], x[0])),
    }


def card_hero(portrait):
    cols = max(len(l) for l in portrait)  # fit the real grid into the left half (x 36..406), centred vertically
    fs = min(9, 370 / (cols * MONO_ADV))
    lh, x0 = fs * 1.125, 36
    y0 = (480 - len(portrait) * lh) / 2 + fs
    rows = ""
    for i, line in enumerate(portrait):
        lead = len(line) - len(line.lstrip())
        if line.strip():
            rows += (f'<text class="mono fade" x="{x0 + lead * fs * MONO_ADV:.1f}" y="{y0 + i * lh:.1f}" '
                     f'font-size="{fs:.2f}"{dl(0.2 + i * 0.018)}>{escape(line.strip())}</text>')
    phrase = textwrap.wrap("I build software you can trust: readable, tested, and honest about what it does.", 33)
    ptxt = "".join(f'<tspan x="430" dy="{0 if i == 0 else 25}">{escape(t)}</tspan>' for i, t in enumerate(phrase))
    sheen = defs = ""
    if ANIM:
        # SMIL moves a soft accent band across "Poma" every 6 s; overlay is hidden under reduced motion
        defs = ('<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="430" y1="0" x2="640" y2="0">'
                f'<stop offset="0" stop-color="{C["accent"]}" stop-opacity="0"/>'
                f'<stop offset=".5" stop-color="{C["accent"]}"/>'
                f'<stop offset="1" stop-color="{C["accent"]}" stop-opacity="0"/>'
                '<animateTransform attributeName="gradientTransform" type="translate" dur="6s" repeatCount="indefinite" '
                'values="-230 0;230 0;230 0" keyTimes="0;.4;1" begin="1.6s"/></linearGradient>')
        sheen = ('<text class="serif sheen" x="430" y="262" font-size="112" fill="url(#sheen)" '
                 'style="opacity:.85">Poma</text>')
    body = (
        f'<g fill="{C["ink"]}">{rows}</g>'
        f'<g fill="{C["ink"]}"><text class="serif rise" x="430" y="160" font-size="112"{dl(0.5)}>Michel</text>'
        f'<g class="rise"{dl(0.7)}><text class="serif" x="430" y="262" font-size="112">Poma</text>{sheen}</g></g>'
        f'<text class="rise" x="430" y="320" font-size="18" fill="{C["grey"]}"{dl(0.95)}>{ptxt}</text>'
        f'<g class="rise"{dl(1.1)}><circle cx="436" cy="410" r="4" fill="{C["accent"]}"/>'
        f'<circle class="pulse" cx="436" cy="410" r="4" fill="{C["accent"]}"/>'
        f'<text class="mono" x="452" y="414" font-size="12" fill="{C["grey"]}">Fullstack developer · Java · Go · React</text></g>'
    )
    return svg(840, 480, "Michel Poma",
               "Fullstack developer. I build software you can trust: readable, tested, and honest about what it does. ASCII portrait.",
               body, ["serif", "sans", "mono"], defs)


def level_fill(lvl):
    if lvl == 0:
        return f'fill="{C["line"]}"'
    return f'fill="{C["accent"]}" fill-opacity="{lvl / 4:.2f}"'


def card_graph(s):
    pitch, cell, x0, y0 = 14.6, 11.4, 32, 78
    mx = max(1, max(n for _, n in s["days"]))
    cols = ""
    for ci, wk in enumerate(s["cal"]["weeks"]):
        cells = ""
        for d in wk["contributionDays"]:
            n = d["contributionCount"]
            row = date.fromisoformat(d["date"]).isoweekday() % 7  # Sunday first
            lvl = 0 if n == 0 else -(-4 * n // mx)
            cells += (f'<rect x="{x0 + ci * pitch:.1f}" y="{y0 + row * pitch:.1f}" width="{cell}" height="{cell}" '
                      f'rx="2.5" {level_fill(lvl)}><title>{escape(d["date"])}: {n}</title></rect>')
        cols += f'<g class="fade"{dl(1.0 + ci * 0.014)}>{cells}</g>'
    ly = y0 + 7 * pitch + 22
    legend = "".join(
        f'<rect x="{688 + i * 16}" y="{ly - 10:.1f}" width="{cell}" height="{cell}" rx="2.5" {level_fill(i)}/>'
        for i in range(5))
    body = (
        f'<text class="serif" x="32" y="46" font-size="28" fill="{C["ink"]}">Contributions</text>'
        f'<text class="mono" x="808" y="44" font-size="12" text-anchor="end" fill="{C["grey"]}">{s["total"]} in the last year</text>'
        f"{cols}"
        f'<text class="mono" x="680" y="{ly:.1f}" font-size="10" text-anchor="end" fill="{C["grey"]}">less</text>{legend}'
        f'<text class="mono" x="776" y="{ly:.1f}" font-size="10" fill="{C["grey"]}">more</text>'
    )
    return svg(840, int(ly + 24), "Contribution graph",
               f"{s['total']} GitHub contributions in the last year, one square per day.", body, ["serif", "mono"])


def card_activity(s):
    base, top, bw, pitch, x0 = 205, 110, 24, 40, 40
    mx = max(1, max(n for _, n in s["months"]))
    best = max(range(12), key=lambda i: (s["months"][i][1], i))
    bars = ""
    for i, (m, n) in enumerate(s["months"]):
        h = max(2, n / mx * top)
        x = x0 + i * pitch
        fill = f'fill="{C["accent"]}"' if i == best else f'fill="{C["grey"]}" fill-opacity=".3"'
        bars += (f'<rect class="bar" x="{x}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="3" {fill}{dl(1.9 + i * 0.05)}>'
                 f'<title>{MONTHS[m]}: {n}</title></rect>'
                 f'<text class="mono" x="{x + bw / 2}" y="{base + 20}" font-size="10" text-anchor="middle" fill="{C["grey"]}">{MONTHS[m]}</text>')
        if i == best:
            bars += (f'<text class="mono fade" x="{x + bw / 2}" y="{base - h - 8:.1f}" font-size="13" text-anchor="middle" '
                     f'fill="{C["accent"]}"{dl(2.6)}>{n}</text>')
    bd, bn = s["busiest"]
    items = [(str(s["streak"]), "current streak, days"), (str(s["active"]), "active days"),
             (str(bn), f"busiest day, {MONTHS[bd.month - 1]} {bd.day}, {bd.year}")]
    stat = ""
    for i, (num, lab) in enumerate(items):
        y = 84 + i * 60
        stat += (f'<g class="rise"{dl(2.2 + i * 0.12)}><text class="mono" x="580" y="{y}" font-size="34" fill="{C["ink"]}">{escape(num)}</text>'
                 f'<text x="580" y="{y + 20}" font-size="12.5" font-weight="500" fill="{C["grey"]}">{escape(lab)}</text></g>')
    body = (f'<text class="serif" x="40" y="48" font-size="28" fill="{C["ink"]}">Activity</text>'
            f'<text class="mono" x="40" y="68" font-size="11" fill="{C["grey"]}">contributions per month</text>'
            f"{bars}{stat}")
    return svg(840, 250, "Activity",
               f"Contributions per month over the last 12 months; best month {MONTHS[s['months'][best][0]]} with {s['months'][best][1]}. "
               f"Current streak {s['streak']} days, {s['active']} active days, busiest day {bd.isoformat()} with {bn}.",
               body, ["serif", "sans500", "mono"])


TILES = {
    "build": ("BUILD", "JackFood", "Food delivery, end to end: React, Spring Boot, Stripe.", "Java · React · MySQL", 2.6),
    "trace": ("TRACE", "Legacy Navigator", "Understand a COBOL system before you change it.", "Go · React · SQLite FTS5", 2.75),
    "replay": ("REPLAY", "Incident Replay", "Fictional incident logs into a timeline and a verifiable postmortem.", "Java · Spring Boot", 2.9),
}


def card_tile(key):
    label, title, text, foot, delay = TILES[key]
    desc = "".join(f'<tspan x="28" dy="{0 if i == 0 else 22}">{escape(t)}</tspan>' for i, t in enumerate(textwrap.wrap(text, 36)))
    body = (
        f'<g class="tile"{dl(delay)}>'
        f'<text class="mono" x="28" y="44" font-size="11" letter-spacing="2" fill="{C["grey"]}">{escape(label)}</text>'
        f'<g class="arrow"><path d="M356 52 L372 36 M360 36 H372 V48" fill="none" stroke="{C["accent"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>'
        f'<text class="serif" x="28" y="108" font-size="42" fill="{C["ink"]}">{escape(title)}</text>'
        f'<rect class="uline" x="28" y="122" width="40" height="2" rx="1" fill="{C["accent"]}"{dl(delay + 0.5)}/>'
        f'<text x="28" y="156" font-size="15" fill="{C["ink"]}">{desc}</text>'
        f'<text class="mono" x="28" y="234" font-size="12" fill="{C["grey"]}">{escape(foot)}</text></g>'
    )
    return svg(400, 260, f"{title} ({label.title()})", f"{title}. {text} {foot}.", body, ["serif", "sans", "mono"])


def main():
    s = stats(ROOT / "data" / "contributions.json")
    portrait = (ROOT / "assets" / "portrait.txt").read_text(encoding="utf-8").splitlines()
    out = {"hero": card_hero(portrait), "graph": card_graph(s), "activity": card_activity(s)}
    out.update({f"tile-{k}": card_tile(k) for k in TILES})
    (ROOT / "cards").mkdir(exist_ok=True)
    for name, doc in out.items():
        (ROOT / "cards" / f"{name}.svg").write_text(doc, encoding="utf-8")
        print(f"cards/{name}.svg {len(doc.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
