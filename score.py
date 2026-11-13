"""Nota de desempenho por partida (parecida com o OP Score) e colocação 1º-10º."""

WEIGHTS = {
    # base: o jogador comparado com os outros 9 da partida
    "kda": 0.8,        # (abates + assistências) / mortes
    "kp": 0.5,         # participação em abates do time
    "dmg": 0.7,        # dano a campeões (fatia do time)
    "taken": 0.15,     # dano recebido + mitigado (fatia do time) – tanques
    "gold": 0.6,       # ouro por minuto
    "cs": 0.15,        # farm por minuto
    "vision": 0.35,    # placar de visão por minuto
    "deaths": -1.4,    # mortes (penalidade)
    "win": 0.6,        # bônus de vitória
    # melhoria 1: contra o rival da mesma rota (suporte x suporte, ADC x ADC...)
    "lane_gold": 0.0,  # diferença de ouro por minuto
    "lane_cs": 0.0,    # diferença de farm por minuto
    "lane_dmg": 0.0,   # diferença de dano a campeões por minuto
    "lane_vision": 0.0,  # diferença de visão por minuto
    # melhoria 2: objetivos
    "obj": 0.0,        # dano em objetivos (torres, dragão, barão) – fatia do time
    "takedowns": 0.0,  # torres + dragões + barões + arautos em que participou
    # melhoria 3: início de jogo contra o rival de rota (linha do tempo)
    "early_gold": 0.0,  # diferença de ouro aos 15 min
    "early_xp": 0.0,    # diferença de XP aos 15 min
    "early_cs": 0.0,    # diferença de farm aos 10 min
}


# Nota v2 (a partir de 13/11/2026): melhorias 1, 2 e 3 (rival de rota, objetivos e início de jogo).
# Pesos calibrados com as 34 colocações do OP.GG da planilha, buscando também equilibrar as rotas
# (colocação média por rota: v1 suporte 6,07 / ADC 5,08 -> v2 todas entre 5,2 e 5,7).
WEIGHTS_V1 = dict(WEIGHTS)
WEIGHTS_V2 = {"kda": 0.8, "kp": 0.79, "dmg": 0.59, "taken": 0.15, "gold": 0.17, "cs": 0.11, "vision": 0.31, "deaths": -1.4, "win": 0.6, "lane_gold": 0.11, "lane_cs": 0.08, "lane_dmg": 0.2, "lane_vision": 0.0, "obj": 0.07, "takedowns": 0.03, "early_gold": 0.17, "early_xp": 0.22, "early_cs": 0.22}
NOTA_V2_DESDE = "2026-11-13"


def pesos_para(dia_iso):
    """Pesos da nota conforme o dia da partida (as partidas antigas mantêm a nota v1)."""
    return WEIGHTS_V2 if dia_iso >= NOTA_V2_DESDE else WEIGHTS_V1


def _ch(p, k):
    return (p.get("challenges") or {}).get(k, 0) or 0


def features(p, team, minutes, rival=None, tl=None):
    tk = sum(x["kills"] for x in team) or 1
    td = sum(x["totalDamageDealtToChampions"] for x in team) or 1
    tt = sum(x["totalDamageTaken"] + x["damageSelfMitigated"] for x in team) or 1
    to = sum(x.get("damageDealtToObjectives", 0) for x in team) or 1
    cs = lambda x: x["totalMinionsKilled"] + x["neutralMinionsKilled"]
    r = rival or p  # sem rival identificado, diferença zero
    tl = tl or {}
    eu, ele = tl.get(p["puuid"]), tl.get(r["puuid"])
    cedo = (lambda k: (eu[k] - ele[k])) if (eu and ele) else (lambda k: 0)
    return {
        "kda": (p["kills"] + p["assists"]) / max(1, p["deaths"]),
        "kp": (p["kills"] + p["assists"]) / tk,
        "dmg": p["totalDamageDealtToChampions"] / td,
        "taken": (p["totalDamageTaken"] + p["damageSelfMitigated"]) / tt,
        "gold": p["goldEarned"] / minutes,
        "cs": cs(p) / minutes,
        "vision": p["visionScore"] / minutes,
        "deaths": p["deaths"],
        "win": 1.0 if p["win"] else 0.0,
        "lane_gold": (p["goldEarned"] - r["goldEarned"]) / minutes,
        "lane_cs": (cs(p) - cs(r)) / minutes,
        "lane_dmg": (p["totalDamageDealtToChampions"] - r["totalDamageDealtToChampions"]) / minutes,
        "lane_vision": (p["visionScore"] - r["visionScore"]) / minutes,
        "obj": p.get("damageDealtToObjectives", 0) / to,
        "takedowns": p.get("turretTakedowns", 0) + _ch(p, "dragonTakedowns") + _ch(p, "baronTakedowns") + _ch(p, "riftHeraldTakedowns"),
        "early_gold": cedo("g15"),
        "early_xp": cedo("x15"),
        "early_cs": cedo("c10"),
    }


def rival_de(p, ps):
    pos = p.get("teamPosition")
    if not pos:
        return None
    return next((x for x in ps if x["teamId"] != p["teamId"] and x.get("teamPosition") == pos), None)


def scores(match, weights=None):
    w_all = weights or WEIGHTS
    info = match["info"]
    minutes = max(1, info["gameDuration"] / 60)
    ps = info["participants"]
    tl = match.get("_tl")  # resumo da linha do tempo, anexado por quem chama
    feats = {p["puuid"]: features(p, [x for x in ps if x["teamId"] == p["teamId"]], minutes, rival_de(p, ps), tl)
             for p in ps}
    out = {k: 0.0 for k in feats}
    for f, w in w_all.items():
        if not w:
            continue
        vals = [v[f] for v in feats.values()]
        mu = sum(vals) / len(vals)
        sd = (sum((x - mu) ** 2 for x in vals) / len(vals)) ** 0.5 or 1
        for k, v in feats.items():
            out[k] += w * (v[f] - mu) / sd
    return out


def rank_match(match, weights=None):
    """puuid -> colocação (1 = melhor)."""
    s = scores(match, weights)
    order = sorted(s, key=lambda k: -s[k])
    return {k: i + 1 for i, k in enumerate(order)}


ARAM_WEIGHTS = {"kda": 0.8, "kp": 0.6, "dmg": 0.9, "taken": 0.25, "gold": 0.5, "deaths": -1.2, "win": 0.6}


def scores_aram(game):
    """Personalizada 3x3 (formato do cliente/LCU): puuid -> nota."""
    minutes = max(1, game["gameDuration"] / 60)
    ident = {i["participantId"]: i["player"] for i in game["participantIdentities"]}
    ps = [{**p["stats"], "teamId": p["teamId"], "puuid": ident[p["participantId"]].get("puuid")}
          for p in game["participants"]]
    feats = {}
    for p in ps:
        team = [x for x in ps if x["teamId"] == p["teamId"]]
        tk = sum(x["kills"] for x in team) or 1
        td = sum(x["totalDamageDealtToChampions"] for x in team) or 1
        tt = sum(x["totalDamageTaken"] + x.get("damageSelfMitigated", 0) for x in team) or 1
        feats[p["puuid"]] = {
            "kda": (p["kills"] + p["assists"]) / max(1, p["deaths"]),
            "kp": (p["kills"] + p["assists"]) / tk,
            "dmg": p["totalDamageDealtToChampions"] / td,
            "taken": (p["totalDamageTaken"] + p.get("damageSelfMitigated", 0)) / tt,
            "gold": p["goldEarned"] / minutes,
            "deaths": p["deaths"],
            "win": 1.0 if p["win"] else 0.0,
        }
    out = {k: 0.0 for k in feats}
    for f, w in ARAM_WEIGHTS.items():
        vals = [v[f] for v in feats.values()]
        mu = sum(vals) / len(vals)
        sd = (sum((x - mu) ** 2 for x in vals) / len(vals)) ** 0.5 or 1
        for k, v in feats.items():
            out[k] += w * (v[f] - mu) / sd
    return out
