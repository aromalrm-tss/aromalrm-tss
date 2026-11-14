#!/usr/bin/env python3
"""Render the last 12 months of contributions as an animated SVG area chart.
Uses the GitHub GraphQL API, so private contributions are included when
'Private contributions' is enabled in your profile's contribution settings."""
import json, os, sys, urllib.request, datetime as dt

G, T, M = "#3DDC84", "#E6EDF3", "#8B949E"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-activity-graph"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[d for d in w["contributionDays"]] for w in cal["weeks"]]
    return cal["totalContributions"], weeks

def render(total, weeks, out):
    W, H, L, R, TOP, B = 900, 280, 56, 28, 78, 46
    pts = [(w[0]["date"], sum(d["contributionCount"] for d in w)) for w in weeks]
    mx = max(1, max(v for _, v in pts))
    step = 1 if mx <= 4 else 5 if mx <= 20 else 10 if mx <= 60 else 25
    top = ((mx + step - 1) // step) * step
    cw, ch = W - L - R, H - TOP - B
    xy = [(L + i * cw / max(1, len(pts) - 1), TOP + ch - v / top * ch) for i, (_, v) in enumerate(pts)]
    d = f"M{xy[0][0]:.1f},{xy[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        mx_ = (x0 + x1) / 2
        d += f" C{mx_:.1f},{y0:.1f} {mx_:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    area = d + f" L{xy[-1][0]:.1f},{TOP+ch} L{xy[0][0]:.1f},{TOP+ch} Z"
    grid = ""
    for k in range(5):
        y = TOP + ch - k * ch / 4
        grid += f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#ffffff" stroke-opacity="0.06"/>'
        grid += f'<text x="{L-10}" y="{y+4:.1f}" font-size="10" fill="{M}" text-anchor="end">{round(top*k/4)}</text>'
    months, last = "", None
    for (ds, _), (x, _) in zip(pts, xy):
        m = dt.date.fromisoformat(ds).strftime("%b")
        if m != last:
            months += f'<text x="{x:.1f}" y="{H-18}" font-size="10" fill="{M}">{m.upper()}</text>'
            last = m
    pi = max(range(len(pts)), key=lambda i: pts[i][1])
    px, py = xy[pi]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="'JetBrains Mono','SF Mono',Consolas,'Liberation Mono',monospace">
<title>Contribution activity, last 12 months</title>
<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{G}" stop-opacity="0.45"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></linearGradient>
<filter id="gl"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0D1117"/><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="#30363D"/>
<text x="{L}" y="34" font-size="13" font-weight="700" fill="{T}" letter-spacing="3">CONTRIBUTION ACTIVITY</text>
<text x="{L}" y="54" font-size="10" fill="{M}" letter-spacing="2">LAST 12 MONTHS · {total} TOTAL · WEEKLY</text>
{grid}{months}
<path d="{area}" fill="url(#a)" opacity="0"><animate attributeName="opacity" from="0" to="1" begin="1.2s" dur="0.8s" fill="freeze"/></path>
<path d="{d}" fill="none" stroke="{G}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" from="1" to="0" dur="1.8s" fill="freeze"/></path>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{G}" filter="url(#gl)" opacity="0"><animate attributeName="opacity" from="0" to="1" begin="1.8s" dur="0.3s" fill="freeze"/></circle>
<text x="{px:.1f}" y="{max(py-12,TOP-4):.1f}" font-size="10" fill="{T}" text-anchor="middle" opacity="0">peak {pts[pi][1]}<animate attributeName="opacity" from="0" to="1" begin="1.9s" dur="0.3s" fill="freeze"/></text>
</svg>'''
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(svg)

if __name__ == "__main__":
    login = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    token = os.environ["GITHUB_TOKEN"]
    out = sys.argv[1] if len(sys.argv) > 1 else "dist/activity.svg"
    total, weeks = fetch(login, token)
    render(total, weeks, out)
