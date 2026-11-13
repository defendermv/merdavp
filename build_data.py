"""Gera os arquivos da página em out/:

- partidas.json  uma linha por jogador do grupo em cada flex válida (ranking MerdaVP);
- aram.json      uma linha por jogador do grupo em cada personalizada (ranking separado);
- placar.json    todos os jogadores de cada partida válida (o placar completo);
- campeoes.json  nome e ícone (data: URL) de cada campeão que aparece, via icons.py.

Regras (planilha MerdaVP):
- vale flex (fila 440) com pelo menos `min_grupo` jogadores do grupo no mesmo time;
- colocação 1º-10º pela nota de score.py; 8º/9º/10º do grupo levam 1/2/3 pontos;
- personalizadas: as três últimas colocações levam 1/2/3 pontos;
- dia = horário de início em Brasília (UTC-3); semana de segunda a domingo.
"""
import json, datetime as dt
from pathlib import Path
from score import scores, scores_aram, pesos_para

HERE = Path(__file__).parent
OUT = HERE / "out"
CFG = json.loads((HERE / "players.json").read_text(encoding="utf-8"))
PUU = json.loads((HERE / "puuids.json").read_text(encoding="utf-8"))
BRT = dt.timezone(dt.timedelta(hours=-3))
ROLE = {"TOP": "TOP", "JUNGLE": "JG", "MIDDLE": "MID", "BOTTOM": "ADC", "UTILITY": "SUP"}
TIME = {100: "azul", 200: "vermelho"}
MAPAS = {12: "ARAM", 11: "Summoner's Rift"}

nick_of = {v["puuid"]: n for n, v in PUU.items() if n in CFG["players"]}
# o cliente do LoL usa outro código de jogador, então as personalizadas casam pelo Riot ID
nick_of_rid = {rid.lower(): n for n, rid in CFG["players"].items()}
ignored = set(CFG.get("partidas_ignoradas", []))


def quando(ms):
    start = dt.datetime.fromtimestamp(ms / 1000, BRT)
    day = start.date()
    return start, day, day - dt.timedelta(days=day.weekday())


def pontos_flex(pos, day):
    """8º/9º/10º = 1/2/3. Desde `mvp_menos_um_desde`, o 1º lugar (MVP) tira 1 ponto."""
    if pos == 1 and day.isoformat() >= CFG.get("mvp_menos_um_desde", "9999"):
        return -1
    return {8: 1, 9: 2, 10: 3}.get(pos, 0)


def flex(m):
    """-> (linhas do ranking, linhas do placar)"""
    info = m["info"]
    if m["metadata"]["matchId"] in ignored or info.get("queueId") != 440 or info["gameDuration"] < 600:
        return [], []
    ps = info["participants"]
    teams = {}
    for p in ps:
        if p["puuid"] in nick_of:
            teams.setdefault(p["teamId"], []).append(p)
    team = max(teams.values(), key=len, default=[])
    if len(team) < CFG["min_grupo"]:
        return [], []
    start, day, week = quando(info["gameStartTimestamp"])
    if day.isoformat() < CFG["inicio"]:
        return [], []
    tl = HERE / "matches" / "timeline" / f'{m["metadata"]["matchId"]}.json'
    if tl.exists():
        m["_tl"] = json.loads(tl.read_text(encoding="utf-8"))
    sc = scores(m, pesos_para(day.isoformat()))
    rank = {k: i + 1 for i, k in enumerate(sorted(sc, key=lambda k: -sc[k]))}
    mid, mins = m["metadata"]["matchId"], round(info["gameDuration"] / 60, 1)
    rows, placar = [], []
    for p in ps:
        r, nick = rank[p["puuid"]], nick_of.get(p["puuid"], "")
        placar.append({
            "partida": mid, "fila": "flex", "time": TIME.get(p["teamId"], str(p["teamId"])),
            "inicio": start.strftime("%Y-%m-%d %H:%M"), "dia": day.isoformat(), "semana": week.isoformat(),
            "minutos": mins, "jogadores": len(ps),
            "vitoria": 1 if p["win"] else 0, "jogador": p.get("riotIdGameName") or "?", "grupo": nick,
            "campeao_id": p["championId"], "nivel": p["champLevel"], "role": ROLE.get(p.get("teamPosition"), ""),
            "abates": p["kills"], "mortes": p["deaths"], "assist": p["assists"],
            "dano": p["totalDamageDealtToChampions"], "ouro": p["goldEarned"],
            "cs": p["totalMinionsKilled"] + p["neutralMinionsKilled"], "visao": p["visionScore"],
            "posicao": r, "nota": round(sc[p["puuid"]], 2),
            "fb": 1 if p.get("firstBloodKill") else 0, "multi": p.get("largestMultiKill", 0),
            "dano_recebido": p.get("totalDamageTaken", 0), "cc": p.get("timeCCingOthers", 0),
            "torres": p.get("turretKills", 0),
        })
        if nick:
            rows.append({
                "partida": mid, "inicio": start.strftime("%Y-%m-%d %H:%M"),
                "dia": day.isoformat(), "semana": week.isoformat(),
                "tipo": f"Flex com {len(team)}", "jogador": nick,
                "campeao_id": p["championId"], "role": ROLE.get(p.get("teamPosition"), "?"),
                "vitoria": 1 if p["win"] else 0,
                "abates": p["kills"], "mortes": p["deaths"], "assist": p["assists"],
                "dano": p["totalDamageDealtToChampions"], "minutos": mins,
                "nota": round(sc[p["puuid"]], 2), "posicao": r,
                "pontos": pontos_flex(r, day), "mvp": 1 if r == 1 else 0,
            })
    return rows, placar


def personalizada(g):
    """Formato do cliente (LCU), 3x3 a 5x5. -> (linhas do ranking, linhas do placar)"""
    if g["gameDuration"] < 300:
        return [], []
    n = len(g["participants"])
    sizes = {}
    for p in g["participants"]:
        sizes[p["teamId"]] = sizes.get(p["teamId"], 0) + 1
    modo = "x".join(str(v) for v in sorted(sizes.values(), reverse=True))
    pts = {n - 2: 1, n - 1: 2, n: 3}
    sc = scores_aram(g)
    rank = {k: i + 1 for i, k in enumerate(sorted(sc, key=lambda k: -sc[k]))}
    ident = {i["participantId"]: i["player"] for i in g["participantIdentities"]}
    start, day, week = quando(g["gameCreation"])
    gid, mins = str(g["gameId"]), round(g["gameDuration"] / 60, 1)
    mapa = MAPAS.get(g.get("mapId"), f"mapa {g.get('mapId')}")
    rows, placar = [], []
    for p in g["participants"]:
        pl, st = ident[p["participantId"]], p["stats"]
        nick = nick_of_rid.get(f'{pl.get("gameName", "")}#{pl.get("tagLine", "")}'.lower(), "")
        r = rank[pl.get("puuid")]
        placar.append({
            "partida": gid, "fila": "personalizada", "time": TIME.get(p["teamId"], str(p["teamId"])),
            "inicio": start.strftime("%Y-%m-%d %H:%M"), "dia": day.isoformat(), "semana": week.isoformat(),
            "minutos": mins, "jogadores": n,
            "vitoria": 1 if st["win"] else 0, "jogador": pl.get("gameName") or "?", "grupo": nick,
            "campeao_id": p["championId"], "nivel": st.get("champLevel", 0), "role": "",
            "abates": st["kills"], "mortes": st["deaths"], "assist": st["assists"],
            "dano": st["totalDamageDealtToChampions"], "ouro": st["goldEarned"],
            "cs": st.get("totalMinionsKilled", 0) + st.get("neutralMinionsKilled", 0),
            "visao": st.get("visionScore", 0), "posicao": r, "nota": round(sc[pl.get("puuid")], 2),
            "fb": 1 if st.get("firstBloodKill") else 0, "multi": st.get("largestMultiKill", 0),
            "dano_recebido": st.get("totalDamageTaken", 0), "cc": st.get("timeCCingOthers", 0),
            "torres": st.get("turretKills", 0),
        })
        if nick:  # quem está fora do grupo conta só para a colocação
            rows.append({
                "partida": gid, "inicio": start.strftime("%Y-%m-%d %H:%M"),
                "dia": day.isoformat(), "semana": week.isoformat(),
                "jogador": nick, "campeao_id": p["championId"],
                "vitoria": 1 if st["win"] else 0,
                "abates": st["kills"], "mortes": st["deaths"], "assist": st["assists"],
                "dano": st["totalDamageDealtToChampions"], "minutos": mins,
                "nota": round(sc[pl.get("puuid")], 2),
                "posicao": r, "jogadores": n, "mvp": 1 if r == 1 else 0,
                "pontos": -1 if r == 1 and day.isoformat() >= CFG.get("mvp_menos_um_desde", "9999") else pts.get(r, 0),
                "modo": modo, "mapa": mapa,
            })
    return rows, placar


def build(folder, fn):
    rows, placar = [], []
    for f in sorted((HERE / "matches" / folder).glob("*.json")):
        r, p = fn(json.loads(f.read_text(encoding="utf-8")))
        rows += r; placar += p
    rows.sort(key=lambda r: (r["inicio"], r["partida"], r["posicao"]))
    return rows, placar


def write(name, data):
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    aram, placar_a = build("custom", personalizada)
    rows, placar_f = build("flex", flex)
    write("aram", aram)
    write("partidas", rows)
    placar = placar_f + placar_a
    tk = {}
    for r in placar:
        k = (r["partida"], r["time"])
        tk[k] = tk.get(k, 0) + r["abates"]
    for r in placar:  # participação em abates (% dos abates do time)
        r["kp"] = round(100 * (r["abates"] + r["assist"]) / max(1, tk[(r["partida"], r["time"])]))
    placar.sort(key=lambda r: (r["partida"], r["time"], r["posicao"]))
    write("placar", placar)
    import icons
    write("campeoes", icons.campeoes({r["campeao_id"] for r in placar}))
    print(f"Personalizadas: {len({r['partida'] for r in aram})} partidas")
    print(f"{len({r['partida'] for r in rows})} partidas válidas, {len(rows)} linhas")


if __name__ == "__main__":
    main()
