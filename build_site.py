"""Monta o site estático em docs/ (publicado pelo GitHub Pages).

- docs/index.html  = page/index.html dentro de um documento HTML completo + site/runtime.js
- docs/data/*.json = os arquivos gerados por build_data.py (out/)

Uso: python build_site.py
"""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
DOCS = HERE / "docs"
FILES = ("partidas", "aram", "placar", "campeoes")

HEAD = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>MerdaVP</title>
<meta name="description" content="Ranking do pior da semana do grupo no League of Legends.">
<link rel="icon" type="image/svg+xml" href="img/icone.svg">
<link rel="icon" type="image/png" sizes="32x32" href="img/favicon.png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<meta name="theme-color" content="#0f161b">
<meta property="og:title" content="MerdaVP">
<meta property="og:description" content="Ranking do pior da semana do grupo no League of Legends.">
<meta property="og:image" content="https://defendermv.github.io/merdavp/img/og.png">
<meta property="og:url" content="https://defendermv.github.io/merdavp/">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@500;600;700;800;900&family=Lilita+One&family=Poppins:wght@400;500;600&display=swap">
<style>
:root { --font-anthropic-sans: "Poppins", "Segoe UI", system-ui, sans-serif; color-scheme: dark; }
html, body { margin: 0; height: 100%; background: #0b1117; }
body { font: 14px/1.45 var(--font-anthropic-sans); -webkit-font-smoothing: antialiased; }
img { max-width: 100%; }
[hidden] { display: none !important; }
.dash-select { appearance: none; -webkit-appearance: none; font: 14px var(--font-anthropic-sans); color: #e1e8f3; padding: 8px 34px 8px 10px; cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%238b9ab2' stroke-width='1.8'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center; }
.mvp .side { height: 100vh; }
@media (max-width: 820px) { .mvp .side { height: auto; } }
</style>
<script src="runtime.js"></script>
</head>
<body>
"""
TAIL = "\n</body>\n</html>\n"


def main():
    page = (HERE / "page" / "index.html").read_text(encoding="utf-8")
    page = page.replace('<meta name="dash-one-writer">', "", 1)
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(HEAD + page + TAIL, encoding="utf-8")
    shutil.copy(HERE / "site" / "runtime.js", DOCS / "runtime.js")
    (DOCS / "img").mkdir(exist_ok=True)
    fontes = {f.name for f in (HERE / "site" / "img").iterdir()}
    for f in (DOCS / "img").iterdir():
        if f.name not in fontes:
            f.unlink()  # remove imagens que saíram do site
    shutil.copytree(HERE / "site" / "img", DOCS / "img", dirs_exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "data").mkdir(exist_ok=True)
    for f in FILES:
        shutil.copy(HERE / "out" / f"{f}.json", DOCS / "data" / f"{f}.json")
    print("site montado em docs/")


if __name__ == "__main__":
    main()
