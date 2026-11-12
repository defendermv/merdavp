"""Nota de desempenho por partida (parecida com o OP Score) e colocação 1º-10º."""

WEIGHTS = {
    # pesos ajustados com as 34 colocações anotadas na planilha (out-nov/2026)
    "kda": 0.8,        # (abates + assistências) / mortes
    "kp": 0.5,         # participação em abates do time
    "dmg": 0.7,        # dano a campeões (fatia do time)
    "taken": 0.15,     # dano recebido + mitigado (fatia do time) – tanques
    "gold": 0.6,       # ouro por minuto
    "cs": 0.15,        # farm por minuto
    "vision": 0.35,    # placar de visão por minuto
    "deaths": -1.4,    # mortes (penalidade)
    "win": 0.6,        # bônus de vitória
}


def features(p, team, minutes):
    tk = sum(x["kills"] for x in team) or 1
    td = sum(x["totalDamageDealtToChampions"] for x in team) or 1
    tt = sum(x["totalDamageTaken"] + x["damageSelfMitigated"] for x in team) or 1
    return {
        "kda": (p["kills"] + p["assists"]) / max(1, p["deaths"]),
        "kp": (p["kills"] + p["assists"]) / tk,
        "dmg": p["totalDamageDealtToChampions"] / td,
        "taken": (p["totalDamageTaken"] + p["damageSelfMitigated"]) / tt,
        "gold": p["goldEarned"] / minutes,
        "cs": (p["totalMinionsKilled"] + p["neutralMinionsKilled"]) / minutes,
        "vision": p["visionScore"] / minutes,
        "deaths": p["deaths"],
        "win": 1.0 if p["win"] else 0.0,
    }


def scores(match):
    info = match["info"]
    minutes = max(1, info["gameDuration"] / 60)
    ps = info["participants"]
    feats = {p["puuid"]: features(p, [x for x in ps if x["teamId"] == p["teamId"]], minutes)
             for p in ps}
    out = {k: 0.0 for k in feats}
    for f, w in WEIGHTS.items():
        vals = [v[f] for v in feats.values()]
        mu = sum(vals) / len(vals)
        sd = (sum((x - mu) ** 2 for x in vals) / len(vals)) ** 0.5 or 1
        for k, v in feats.items():
            out[k] += w * (v[f] - mu) / sd
    return out


def rank_match(match):
    """puuid -> colocação (1 = melhor)."""
    s = scores(match)
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
