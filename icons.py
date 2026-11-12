"""Nomes e ícones dos campeões a partir do Data Dragon (CDN oficial da Riot).

Os ícones são guardados em cache/icons e entram na página como data: URLs
(a página não pode carregar imagens de outros sites).
"""
import base64, io, json, urllib.request
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
CACHE = HERE / "cache"
DD = "https://ddragon.leagueoflegends.com"
SIZE = 48


def _json(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)


def _catalogo():
    """{key numérica: {"id": "MonkeyKing", "nome": "Wukong"}}, com cache por versão."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / "champions.json"
    try:
        v = _json(f"{DD}/api/versions.json")[0]
    except Exception:
        v = None
    if f.exists():
        c = json.loads(f.read_text(encoding="utf-8"))
        if v is None or c["versao"] == v:
            return c
    data = _json(f"{DD}/cdn/{v}/data/pt_BR/champion.json")["data"]
    c = {"versao": v, "campeoes": {d["key"]: {"id": d["id"], "nome": d["name"]} for d in data.values()}}
    f.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return c


def _icone(versao, cid):
    f = CACHE / "icons" / f"{cid}.webp"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{DD}/cdn/{versao}/img/champion/{cid}.png", timeout=20) as r:
            img = Image.open(io.BytesIO(r.read())).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
        img.save(f, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(f.read_bytes()).decode()


def campeoes(keys):
    cat = _catalogo()
    out = []
    for k in sorted(keys):
        c = cat["campeoes"].get(str(k))
        if not c:
            out.append({"campeao_id": k, "nome": f"#{k}", "icone": ""}); continue
        try:
            ico = _icone(cat["versao"], c["id"])
        except Exception:
            ico = ""
        out.append({"campeao_id": k, "nome": c["nome"], "icone": ico})
    return out
