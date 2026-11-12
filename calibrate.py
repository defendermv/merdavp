"""Cruza as linhas da planilha com as partidas da API e compara colocações."""
import json, re, sys
import openpyxl
from score import rank_match

XLSX = r"C:\Users\marvi\OneDrive\DESIGN\Defender\MerdaVP 2025.xlsx"
ms = json.load(open("defender_flex.json", encoding="utf-8"))

wb = openpyxl.load_workbook(XLSX, data_only=True)
rows = [r[:7] for ws in wb.worksheets for r in ws.iter_rows(min_row=2, values_only=True)
        if r[0] and r[3]]

def norm(s): return re.sub(r"[^a-z]", "", s.lower())

alias, results = {}, []
for r in rows:
    t = int(re.search(r"/(\d{13})", r[3]).group(1))
    m = min(ms, key=lambda m: abs(m["info"]["gameEndTimestamp"] - t))
    if abs(m["info"]["gameEndTimestamp"] - t) > 600_000:
        results.append((r, None, None)); continue
    ranks = rank_match(m)
    p = next((p for p in m["info"]["participants"]
              if norm(p["championName"]) == norm(r[4])), None)
    if not p:
        results.append((r, m, None)); continue
    alias[r[0]] = f'{p["riotIdGameName"]}#{p["riotIdTagline"]}'
    results.append((r, m, ranks[p["puuid"]]))

hit = near = n = 0
for r, m, rk in results:
    want = int(re.sub(r"\D", "", r[6]))
    if rk is None:
        print(f"{r[0]:14} {r[4]:10} planilha {want}º  -> partida não encontrada"); continue
    n += 1; hit += rk == want; near += rk >= 8
    print(f"{r[0]:14} {r[4]:10} planilha {want}º  fórmula {rk}º {'OK' if rk == want else ('~' if rk >= 8 else 'X')}")
print(f"\npartidas casadas: {n}/{len(rows)} | posição exata: {hit} | ficou entre 8º-10º: {near}")
print("apelidos:", json.dumps(alias, ensure_ascii=False, indent=1))
