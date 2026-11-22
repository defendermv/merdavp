"""Gera os arquivos da página em out/:

- partidas.json  uma linha por jogador do grupo em cada partida de flex (ranking flex);
- aram.json      uma linha por jogador do grupo em cada personalizada de ARAM (ranking do ARAM);
- placar.json    todos os jogadores de cada partida válida (o placar completo);
- campeoes.json  nome e ícone (data: URL) de cada campeão que aparece, via icons.py;
- config.json    regras da temporada (datas, mínimo de partidas, valores do pix, partidas anuladas).

Regras (temporadas mensais, a partir de 16/11/2026):
- vale flex (fila 440) com pelo menos `min_grupo` jogadores do grupo no mesmo time;
- vale também personalizada 5x5 na Summoner's Rift com pelo menos `min_grupo` jogadores do grupo
  na partida: ela entra no ranking da flex, com o mesmo algoritmo de nota;
- personalizada no ARAM vale só para o ranking do ARAM;
- colocação 1º-10º pela nota de score.py. Os três últimos levam 1/2/3 pontos (8º/9º/10º) e os
  três primeiros tiram 3/2/1 (1º/2º/3º). Quem tem menos pontos por partida é o MVP da temporada;
  quem tem mais é o MerdaVP;
- dia = horário de início em Brasília (UTC-3); temporada: do dia 8 ao dia 7 do mês seguinte
  (a primeira começa em 16/11). No JSON o campo `semana` guarda a data de início da temporada;
- cada partida válida recebe um número fixo (numeracao.json), para apontar partidas anuladas.
"""
import json, datetime as dt
from pathlib import Path
from score import scores, scores_aram, pesos_para

HERE = Path(__file__).parent
OUT = HERE / "out"
CFG = json.loads((HERE / "players.json").read_text(encoding="utf-8"))
PUU = json.loads((HERE / "puuids.json").read_text(encoding="utf-8"))
NUM_FILE = HERE / "numeracao.json"
BRT = dt.timezone(dt.timedelta(hours=-3))
ROLE = {"TOP": "TOP", "JUNGLE": "JG", "MIDDLE": "MID", "BOTTOM": "ADC", "UTILITY": "SUP"}
TIME = {100: "azul", 200: "vermelho"}
MAPA_SR, MAPA_ARAM = 11, 12

nick_of = {v["puuid"]: n for n, v in PUU.items() if n in CFG["players"]}
# contas extras (ex.: conta nova do Braga) contam para o mesmo apelido
for _n, _v in PUU.items():
    if _n in CFG["players"]:
        nick_of.update({pu: _n for pu in _v.get("extras", {}).values()})
# o cliente do LoL usa outro código de jogador, então as personalizadas casam pelo Riot ID
nick_of_rid = {rid.lower(): n for n, rid in CFG["players"].items()}
for _n, _rids in CFG.get("contas_extras", {}).items():
    if _n in CFG["players"]:
        nick_of_rid.update({r.lower(): _n for r in _rids})
PRIMEIRA = dt.date.fromisoformat(CFG["temporada"]["primeira"])
VIRADA = CFG["temporada"]["dia_virada"]


def temporada_de(day):
    """Dia -> data de início da temporada em que ele cai (dia 8; a primeira começa em 16/11)."""
    if day.day >= VIRADA:
        ini = day.replace(day=VIRADA)
    else:
        ini = (day.replace(day=1) - dt.timedelta(days=1)).replace(day=VIRADA)
    return max(ini, PRIMEIRA)


def quando(ms):
    start = dt.datetime.fromtimestamp(ms / 1000, BRT)
    day = start.date()
    return start, day, temporada_de(day)


def pontos_posicao(pos, n):
    """Últimos três: +1/+2/+3 (n-2º, n-1º, nº). Primeiros três: -3/-2/-1 (1º, 2º, 3º)."""
    return {n - 2: 1, n - 1: 2, n: 3}.get(pos, 0) + {1: -3, 2: -2, 3: -1}.get(pos, 0)


# ---------- partidas de flex (e personalizadas 5x5 que valem como flex) ----------
def _flex_like(m, nick_fn, tipo, origem):
    """m no formato da API da Riot (Match-V5). -> (linhas do ranking, linhas do placar)"""
    info = m["info"]
    ps = info["participants"]
    start, day, temp = quando(info["gameStartTimestamp"])
    if day.isoformat() < CFG["inicio"]:
        return [], []
    mid = m["metadata"]["matchId"]
    tl = HERE / "matches" / "timeline" / f"{mid}.json"
    if tl.exists():
        m["_tl"] = json.loads(tl.read_text(encoding="utf-8"))
    sc = scores(m, pesos_para(day.isoformat()))
    rank = {k: i + 1 for i, k in enumerate(sorted(sc, key=lambda k: -sc[k]))}
    mins = round(info["gameDuration"] / 60, 1)
    inicio, week = start.strftime("%Y-%m-%d %H:%M"), temp.isoformat()
    rows, placar = [], []
    for p in ps:
        r, nick = rank[p["puuid"]], nick_fn(p)
        placar.append({
            "partida": mid, "fila": "flex", "origem": origem, "time": TIME.get(p["teamId"], str(p["teamId"])),
            "inicio": inicio, "dia": day.isoformat(), "semana": week,
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
                "partida": mid, "inicio": inicio, "dia": day.isoformat(), "semana": week,
                "tipo": tipo, "origem": origem, "jogador": nick,
                "campeao_id": p["championId"], "role": ROLE.get(p.get("teamPosition"), "?"),
                "vitoria": 1 if p["win"] else 0,
                "abates": p["kills"], "mortes": p["deaths"], "assist": p["assists"],
                "dano": p["totalDamageDealtToChampions"], "minutos": mins,
                "nota": round(sc[p["puuid"]], 2), "posicao": r,
                "pontos": pontos_posicao(r, len(ps)), "mvp": 1 if r == 1 else 0,
            })
    return rows, placar


def flex(m):
    info = m["info"]
    if info.get("queueId") != 440 or info["gameDuration"] < 600:
        return [], []
    teams = {}
    for p in info["participants"]:
        if p["puuid"] in nick_of:
            teams.setdefault(p["teamId"], []).append(p)
    team = max(teams.values(), key=len, default=[])
    if len(team) < CFG["min_grupo"]:
        return [], []
    return _flex_like(m, lambda p: nick_of.get(p["puuid"], ""), f"Flex com {len(team)}", "flex")


# posição pelo cliente do LoL (lane/role) -> teamPosition da API
POS_LCU = {("TOP", "SOLO"): "TOP", ("JUNGLE", "NONE"): "JUNGLE", ("MIDDLE", "SOLO"): "MIDDLE",
           ("BOTTOM", "CARRY"): "BOTTOM", ("BOTTOM", "SUPPORT"): "UTILITY"}


def lcu_para_v5(g):
    """Personalizada do cliente (LCU) -> formato Match-V5, para usar o mesmo algoritmo da flex."""
    ident = {i["participantId"]: i["player"] for i in g["participantIdentities"]}
    ps = []
    for p in g["participants"]:
        st, pl = p["stats"], ident[p["participantId"]]
        tl = p.get("timeline") or {}
        ps.append({**st, "puuid": pl.get("puuid") or f'p{p["participantId"]}', "teamId": p["teamId"],
                   "championId": p["championId"], "riotIdGameName": pl.get("gameName"), "riotIdTagline": pl.get("tagLine"),
                   "teamPosition": POS_LCU.get((tl.get("lane"), tl.get("role")), ""),
                   "turretTakedowns": st.get("turretKills", 0)})
    for tid in {x["teamId"] for x in ps}:  # a rota só vale se o time tiver as 5 rotas, sem repetir
        time = [x for x in ps if x["teamId"] == tid]
        if len({x["teamPosition"] for x in time}) != 5 or any(not x["teamPosition"] for x in time):
            for x in time:
                x["teamPosition"] = ""
    return {"metadata": {"matchId": str(g["gameId"])},
            "info": {"gameDuration": g["gameDuration"], "gameStartTimestamp": g["gameCreation"], "queueId": 0, "participants": ps}}


def personalizada_flex(g):
    """Personalizada 5x5 na Summoner's Rift com 3 ou mais do grupo: vale como flex."""
    if g.get("mapId") != MAPA_SR or len(g["participants"]) != 10 or g["gameDuration"] < 600:
        return [], []
    m = lcu_para_v5(g)
    nick_fn = lambda p: nick_of_rid.get(f'{p.get("riotIdGameName") or ""}#{p.get("riotIdTagline") or ""}'.lower(), "")
    n = sum(1 for p in m["info"]["participants"] if nick_fn(p))
    if n < CFG["min_grupo"]:
        return [], []
    return _flex_like(m, nick_fn, f"Personalizada 5x5 com {n}", "personalizada")


# ---------- personalizadas de ARAM ----------
def personalizada_aram(g):
    """Personalizada no ARAM (formato do cliente, LCU). -> (linhas do ranking, linhas do placar)"""
    if g.get("mapId") != MAPA_ARAM or g["gameDuration"] < 300:
        return [], []
    n = len(g["participants"])
    sizes = {}
    for p in g["participants"]:
        sizes[p["teamId"]] = sizes.get(p["teamId"], 0) + 1
    modo = "x".join(str(v) for v in sorted(sizes.values(), reverse=True))
    sc = scores_aram(g)
    rank = {k: i + 1 for i, k in enumerate(sorted(sc, key=lambda k: -sc[k]))}
    ident = {i["participantId"]: i["player"] for i in g["participantIdentities"]}
    start, day, temp = quando(g["gameCreation"])
    if day.isoformat() < CFG["inicio"]:
        return [], []
    gid, mins = str(g["gameId"]), round(g["gameDuration"] / 60, 1)
    inicio, week = start.strftime("%Y-%m-%d %H:%M"), temp.isoformat()
    rows, placar = [], []
    for p in g["participants"]:
        pl, st = ident[p["participantId"]], p["stats"]
        nick = nick_of_rid.get(f'{pl.get("gameName", "")}#{pl.get("tagLine", "")}'.lower(), "")
        r = rank[pl.get("puuid")]
        placar.append({
            "partida": gid, "fila": "personalizada", "origem": "personalizada", "time": TIME.get(p["teamId"], str(p["teamId"])),
            "inicio": inicio, "dia": day.isoformat(), "semana": week,
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
                "partida": gid, "inicio": inicio, "dia": day.isoformat(), "semana": week,
                "jogador": nick, "campeao_id": p["championId"],
                "vitoria": 1 if st["win"] else 0,
                "abates": st["kills"], "mortes": st["deaths"], "assist": st["assists"],
                "dano": st["totalDamageDealtToChampions"], "minutos": mins,
                "nota": round(sc[pl.get("puuid")], 2),
                "posicao": r, "jogadores": n, "mvp": 1 if r == 1 else 0,
                "pontos": pontos_posicao(r, n),
                "modo": modo, "mapa": "ARAM",
            })
    return rows, placar


def carrega(folder, fn):
    rows, placar = [], []
    for f in sorted((HERE / "matches" / folder).glob("*.json")):
        r, p = fn(json.loads(f.read_text(encoding="utf-8")))
        rows += r; placar += p
    return rows, placar


# ---------- numeração das partidas ----------
def numerar(placar_all):
    """Dá um número fixo a cada partida válida (guardado em numeracao.json).
    Partida nova ganha o próximo número livre; o número nunca muda nem é reaproveitado."""
    reg = json.loads(NUM_FILE.read_text(encoding="utf-8")) if NUM_FILE.exists() else {}
    vistas = {}
    for r in placar_all:
        vistas.setdefault(r["partida"], (r["inicio"], r["origem"] if r["fila"] == "flex" else "aram"))
    proximo = max((v["n"] for v in reg.values()), default=0) + 1
    for mid, (inicio, tipo) in sorted(vistas.items(), key=lambda kv: (kv[1][0], kv[0])):
        if mid not in reg:
            reg[mid] = {"n": proximo, "tipo": tipo, "inicio": inicio}
            proximo += 1
    NUM_FILE.write_text(json.dumps(dict(sorted(reg.items(), key=lambda kv: kv[1]["n"])), ensure_ascii=False, indent=1), encoding="utf-8")
    return reg


def anuladas(reg):
    """Conjunto de ids das partidas anuladas (a lista aceita número ou id)."""
    por_numero = {v["n"]: k for k, v in reg.items()}
    ids = set()
    for x in CFG.get("partidas_anuladas", []) + CFG.get("partidas_ignoradas", []):
        ids.add(por_numero.get(x, str(x)) if isinstance(x, int) else str(x))
    return ids


def write(name, data):
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    aram, placar_a = carrega("custom", personalizada_aram)
    rows_c, placar_c = carrega("custom", personalizada_flex)
    rows_f, placar_f = carrega("flex", flex)
    rows, placar_f = rows_f + rows_c, placar_f + placar_c
    reg = numerar(placar_f + placar_a)
    anul = anuladas(reg)
    for lista in (aram, rows, placar_f, placar_a):
        lista[:] = [r for r in lista if r["partida"] not in anul]
        for r in lista:
            r["numero"] = reg[r["partida"]]["n"]
    rows.sort(key=lambda r: (r["inicio"], r["partida"], r["posicao"]))
    aram.sort(key=lambda r: (r["inicio"], r["partida"], r["posicao"]))
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
    write("config", [{
        "primeira": CFG["temporada"]["primeira"], "dia_virada": VIRADA,
        "minimo_partidas": CFG["minimo_partidas"], "inscricao": CFG["inscricao"], "punicao": CFG["punicao"],
        "jogadores": list(CFG["players"]),
        "anuladas": sorted({reg[i]["n"] for i in anul if i in reg}),
    }])
    import icons
    write("campeoes", icons.campeoes({r["campeao_id"] for r in placar}))
    print(f"ARAM: {len({r['partida'] for r in aram})} partidas")
    print(f"Flex: {len({r['partida'] for r in rows})} partidas válidas, {len(rows)} linhas "
          f"({len({r['partida'] for r in rows_c if r['partida'] not in anul})} são personalizadas 5x5)")
    print(f"Numeradas: {len(reg)} (anuladas: {sorted(reg[i]['n'] for i in anul if i in reg)})")


if __name__ == "__main__":
    main()
