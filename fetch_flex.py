"""Busca as flex (fila 440) de todos os jogadores e guarda em matches/flex/<id>.json.
Também guarda o resumo da linha do tempo de cada partida em matches/timeline/<id>.json
(ouro, XP e farm de cada jogador aos 10 e aos 15 minutos).

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
TL = HERE / "matches" / "timeline"
TL.mkdir(parents=True, exist_ok=True)


def resumo_timeline(match_id, match):
    """Baixa a linha do tempo e guarda só o essencial: {puuid: {g10,g15,x10,x15,c10,c15}}."""
    tl = riot.get(f"{riot.REGIONAL}/lol/match/v5/matches/{match_id}/timeline")
    frames = tl["info"]["frames"]
    pid_puuid = {p["participantId"]: p["puuid"] for p in tl["info"]["participants"]} if "participants" in tl["info"]         else {p["participantId"]: p["puuid"] for p in match["info"]["participants"]}
    def em(minuto):
        return frames[min(minuto, len(frames) - 1)]["participantFrames"]
    out = {}
    for pid, pu in pid_puuid.items():
        f10, f15 = em(10)[str(pid)], em(15)[str(pid)]
        out[pu] = {"g10": f10["totalGold"], "g15": f15["totalGold"], "x10": f10["xp"], "x15": f15["xp"],
                   "c10": f10["minionsKilled"] + f10["jungleMinionsKilled"], "c15": f15["minionsKilled"] + f15["jungleMinionsKilled"]}
    return out


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
    faltam = [f for f in sorted(OUT.glob("*.json")) if not (TL / f.name).exists()]
    for f in faltam:
        m = json.loads(f.read_text(encoding="utf-8"))
        (TL / f.name).write_text(json.dumps(resumo_timeline(f.stem, m)), encoding="utf-8")
    print(f"linhas do tempo baixadas: {len(faltam)}")


if __name__ == "__main__":
    main()
