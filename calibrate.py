"""Calibra os pesos da nota da flex contra as colocações do OP.GG anotadas na planilha.

Uso: python calibrate.py
Mostra o acerto da nota atual e procura pesos melhores (busca aleatória),
com uma validação cruzada simples (ajusta numa metade, testa na outra).
"""
import json, random, re, statistics
from pathlib import Path
import openpyxl
import score

XLSX = r"C:\Users\marvi\OneDrive\DESIGN\Defender\MerdaVP 2025.xlsx"
HERE = Path(__file__).parent
ms = []
for f in (HERE / "matches" / "flex").glob("*.json"):
    m = json.loads(f.read_text(encoding="utf-8"))
    t = HERE / "matches" / "timeline" / f.name
    if t.exists():
        m["_tl"] = json.loads(t.read_text(encoding="utf-8"))
    ms.append(m)
norm = lambda s: re.sub(r"[^a-z]", "", s.lower())

casos = []
wb = openpyxl.load_workbook(XLSX, data_only=True)
for ws in wb.worksheets:
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not (r[0] and r[3]):
            continue
        t = int(re.search(r"/(\d{13})", r[3]).group(1))
        m = min(ms, key=lambda m: abs(m["info"]["gameEndTimestamp"] - t))
        if abs(m["info"]["gameEndTimestamp"] - t) > 600_000:
            continue
        p = next((p for p in m["info"]["participants"] if norm(p["championName"]) == norm(r[4])), None)
        if p:
            casos.append((m, p["puuid"], int(re.sub(r"\D", "", r[6])), r[0], r[4]))


def avalia(w, cs=casos):
    faixa = exato = 0; erro = 0
    for m, pu, alvo, *_ in cs:
        rk = score.rank_match(m, w)[pu]
        faixa += rk >= 8; exato += rk == alvo; erro += abs(rk - alvo)
    return faixa, exato, erro


def melhor(cs, base, livres, iters=3000, seed=1):
    rnd = random.Random(seed); best = (avalia(base, cs), base)
    for _ in range(iters):
        w = dict(base)
        for k in livres:
            v = base[k] if base[k] else 0.4
            w[k] = round(rnd.uniform(-0.2, 1.6) * v if k != "deaths" else -rnd.uniform(0.6, 2.0), 2)
        r = avalia(w, cs)
        if (r[0], r[1], -r[2]) > (best[0][0], best[0][1], -best[0][2]):
            best = (r, w)
    return best


def vies_suporte(w):
    """Colocação média de cada rota em todas as partidas (neutro ~5,5)."""
    pos = {}
    for m in ms:
        rk = score.rank_match(m, w)
        for p in m["info"]["participants"]:
            pos.setdefault(p.get("teamPosition") or "?", []).append(rk[p["puuid"]])
    return {k: round(statistics.mean(v), 2) for k, v in sorted(pos.items()) if k != "?"}


if __name__ == "__main__":
    print(f"{len(casos)} casos da planilha casados com partidas")
    antigo = dict(score.WEIGHTS)
    print("nota antiga  -> faixa 8º-10º, exato, erro total:", avalia(antigo), vies_suporte(antigo))
    novos = ["lane_gold", "lane_cs", "lane_dmg", "lane_vision", "obj", "takedowns"]
    livres = novos + ["gold", "cs", "dmg", "vision", "kda", "deaths", "taken"]
    # validação cruzada: ajusta numa metade e mede na outra
    rnd = random.Random(7); idx = list(range(len(casos))); rnd.shuffle(idx)
    A = [casos[i] for i in idx[::2]]; B = [casos[i] for i in idx[1::2]]
    for nome, tr, te in (("A->B", A, B), ("B->A", B, A)):
        r, w = melhor(tr, antigo, livres, 2000)
        print(f"validação {nome}: antiga no teste {avalia(antigo, te)} | nova no teste {avalia(w, te)}")
    r, w = melhor(casos, antigo, livres, 4000)
    print("nota nova    -> faixa 8º-10º, exato, erro total:", r, vies_suporte(w))
    print("pesos:", json.dumps(w))
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "pesos-calibrados.json").write_text(json.dumps(w, indent=1), encoding="utf-8")
