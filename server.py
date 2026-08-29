from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from roomgen.config import DENSITIES, DIFFICULTIES, LAYOUT_TYPES, GenerationParams
from roomgen.generator import generate_rooms

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"


INDEX = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Room Generator</title>
  <style>
    :root { color-scheme: dark; --bg:#111319; --panel:#191d27; --line:#303748; --text:#f4f7fb; --muted:#9aa6b2; --accent:#58c7ff; --ok:#74e68b; --bad:#ff6d6d; }
    * { box-sizing:border-box; }
    body { margin:0; font:14px/1.45 Inter,Segoe UI,Arial,sans-serif; background:var(--bg); color:var(--text); }
    main { max-width:1180px; margin:0 auto; padding:24px; }
    h1 { margin:0 0 6px; font-size:26px; }
    .top { display:flex; justify-content:space-between; gap:16px; align-items:flex-end; margin-bottom:18px; }
    .muted { color:var(--muted); }
    .grid { display:grid; grid-template-columns:340px 1fr; gap:18px; align-items:start; }
    form, .results { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }
    label { display:block; margin:0 0 12px; color:var(--muted); font-weight:700; }
    input, select { width:100%; margin-top:6px; padding:10px 11px; border-radius:6px; border:1px solid var(--line); background:#0d1017; color:var(--text); }
    .two { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    button { width:100%; border:0; border-radius:6px; padding:12px 14px; background:var(--accent); color:#061018; font-weight:900; cursor:pointer; }
    .stats { display:grid; grid-template-columns:repeat(5,minmax(110px,1fr)); gap:10px; margin-bottom:14px; }
    .stat { border:1px solid var(--line); border-radius:8px; padding:10px; background:#10141d; }
    .stat strong { display:block; font-size:20px; }
    .rooms { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:12px; }
    .room { border:1px solid var(--line); border-radius:8px; padding:10px; background:#10141d; }
    .room img { width:100%; image-rendering:pixelated; background:white; border:1px solid #2d3546; }
    .room footer { display:flex; gap:8px; margin-top:8px; }
    .room a { flex:1; text-align:center; color:var(--text); text-decoration:none; border:1px solid var(--line); padding:6px; border-radius:6px; }
    .ok { color:var(--ok); } .bad { color:var(--bad); }
    @media (max-width: 820px) { .grid { grid-template-columns:1fr; } .top { display:block; } }
  </style>
</head>
<body>
<main>
  <div class="top">
    <div>
      <h1>AI Room Generator</h1>
      <div class="muted">Deterministic pixel-perfect PNG maps. 1 pixel = 1 game meter.</div>
    </div>
    <div class="muted">No n8n. No image generation. Validator before output.</div>
  </div>
  <div class="grid">
    <form method="post" action="/generate">
      <div class="two">
        <label>Room Width <input name="width" type="number" value="80" min="16" max="512"></label>
        <label>Room Height <input name="height" type="number" value="40" min="12" max="512"></label>
      </div>
      <div class="two">
        <label>Doors <input name="doors" type="number" value="2" min="1" max="6"></label>
        <label>Enemies <input name="enemies" type="number" value="5" min="0" max="50"></label>
      </div>
      <label>Difficulty <select name="difficulty">{difficulty_options}</select></label>
      <label>Platform Density <select name="platform_density">{density_options}</select></label>
      <label>Decor Density <select name="decor_density">{density_options}</select></label>
      <label>Layout Type <select name="layout_type">{layout_options}</select></label>
      <div class="two">
        <label>Number of Rooms <input name="number_of_rooms" type="number" value="20" min="1" max="60"></label>
        <label>Seed <input name="seed" type="number" value="12345"></label>
      </div>
      <button type="submit">GENERATE</button>
    </form>
    <section class="results">{results}</section>
  </div>
</main>
</body>
</html>"""


def options(values: tuple[str, ...], selected: str = "medium") -> str:
    return "".join(
        f'<option value="{value}"{" selected" if value == selected else ""}>{value}</option>' for value in values
    )


def render_page(report: dict | None = None) -> bytes:
    if report is None:
        results = '<p class="muted">Click GENERATE to create room PNG and JSON files.</p>'
    else:
        cards = []
        for room in report["rooms"]:
            idx = room["room_id"]
            status = "ok" if room["valid"] else "bad"
            cards.append(
                f'<article class="room"><strong>room_{idx:03d}</strong> '
                f'<span class="{status}">{"valid" if room["valid"] else "invalid"}</span>'
                f'<img src="/output/room_{idx:03d}.png?cache={report["parameters"]["seed"]}" alt="room {idx}">'
                f'<footer><a href="/output/room_{idx:03d}.png" download>PNG</a>'
                f'<a href="/output/room_{idx:03d}.json" download>JSON</a></footer></article>'
            )
        results = f"""
        <div class="stats">
          <div class="stat"><span>Generated</span><strong>{report['generated']}</strong></div>
          <div class="stat"><span>Valid</span><strong>{report['valid']}</strong></div>
          <div class="stat"><span>Invalid</span><strong>{report['invalid']}</strong></div>
          <div class="stat"><span>Retries</span><strong>{report['retries']}</strong></div>
          <div class="stat"><span>Avg time</span><strong>{report['average_generation_time']}s</strong></div>
        </div>
        <p><a href="/output/generation_report.json" download>Download generation_report.json</a></p>
        <div class="rooms">{''.join(cards)}</div>
        """
    page = INDEX.replace("{difficulty_options}", options(DIFFICULTIES))
    page = page.replace("{density_options}", options(DENSITIES))
    page = page.replace("{layout_options}", options(LAYOUT_TYPES, "industrial"))
    page = page.replace("{results}", results)
    return page.encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            payload = render_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path.startswith("/output/"):
            self.directory = str(ROOT)
            return super().do_GET()
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        fields = parse_qs(self.rfile.read(length).decode("utf-8"))
        value = lambda name, default: fields.get(name, [default])[0]
        params = GenerationParams(
            width=int(value("width", 80)),
            height=int(value("height", 40)),
            doors=int(value("doors", 2)),
            enemies=int(value("enemies", 5)),
            difficulty=value("difficulty", "medium"),
            platform_density=value("platform_density", "medium"),
            decor_density=value("decor_density", "medium"),
            layout_type=value("layout_type", "industrial"),
            number_of_rooms=int(value("number_of_rooms", 20)),
            seed=int(value("seed", 12345)),
        )
        report = generate_rooms(params, OUTPUT)
        payload = render_page(report)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:`n    import os`n    host = os.environ.get("ROOMGEN_HOST", "127.0.0.1")`n    port = int(os.environ.get("ROOMGEN_PORT", "8010"))`n    server = ThreadingHTTPServer((host, port), Handler)`n    print(f"AI Room Generator running at http://{host}:{port}")`n    server.serve_forever()


if __name__ == "__main__":
    main()


