"""Busca as flex (fila 440) de todos os jogadores e guarda em matches/flex/<id>.json.

Uso: python fetch_flex.py
Só baixa partidas novas; pode rodar quantas vezes quiser.
"""
import json, datetime as dt
from pathlib import Path
import riot

HERE = Path(__file__).parent
CFG = json.loads((HERE / "players.json").read_text(encoding="utf-8"))
OUT = HERE / "matches" / "flex"
OUT.mkdir(parents=True, exist_ok=True)
PUUIDS = HERE / "puuids.json"


def puuids():
    cache = json.loads(PUUIDS.read_text(encoding="utf-8")) if PUUIDS.exists() else {}
    for nick, rid in CFG["players"].items():
        if cache.get(nick, {}).get("riot_id") != rid:
            name, tag = rid.split("#")
            cache[nick] = {"riot_id": rid, "puuid": riot.account(name, tag)["puuid"]}
    PUUIDS.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return {n: v["puuid"] for n, v in cache.items() if n in CFG["players"]}


def main():
    start = dt.datetime.fromisoformat(CFG["inicio"]).timestamp()
    new = 0
    for nick, pu in puuids().items():
        ids, offset = [], 0
        while True:  # pagina de 100 em 100
            page = riot.get(f"{riot.REGIONAL}/lol/match/v5/matches/by-puuid/{pu}/ids",
                            {"queue": 440, "startTime": int(start), "start": offset, "count": 100})
            ids += page
            if len(page) < 100: break
            offset += 100
        for mid in ids:
            f = OUT / f"{mid}.json"
            if not f.exists():
                f.write_text(json.dumps(riot.match(mid), ensure_ascii=False), encoding="utf-8")
                new += 1
        print(f"{nick}: {len(ids)} flex")
    print(f"novas partidas baixadas: {new}")


if __name__ == "__main__":
    main()
