"""Atualização diária: busca flex novas, roda o coletor das personalizadas e
recalcula os arquivos da página. Imprime um resumo em JSON na última linha:
{"ok": bool, "erro": str|null, "mudou": {"partidas", "aram", "placar", "campeoes": bool}, ...}
"""
import hashlib, json, sys, traceback, urllib.error
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
ENVIADO = HERE / "out" / "enviado.json"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    res = {"ok": True, "erro": None}
    import fetch_flex, fetch_custom, build_data
    try:
        fetch_flex.main()
    except urllib.error.HTTPError as e:
        res["ok"] = False
        res["erro"] = ("chave da API da Riot recusada (expirou ou é inválida): troque em app/.env"
                       if e.code in (401, 403) else f"API da Riot respondeu {e.code}")
    except Exception as e:
        res["ok"] = False; res["erro"] = f"falha ao buscar flex: {e!r}"
    try:
        fetch_custom.main()
    except Exception as e:
        print("coletor:", repr(e))
    build_data.main()
    sent = json.loads(ENVIADO.read_text(encoding="utf-8")) if ENVIADO.exists() else {}
    res["mudou"] = {}
    for nome in ("partidas", "aram", "placar", "campeoes"):
        f = HERE / "out" / f"{nome}.json"
        res["mudou"][nome] = sha(f) != sent.get(nome)
        res[f"arquivo_{nome}"] = str(f)
    res["partidas_flex"] = len({r["partida"] for r in json.loads((HERE / "out" / "partidas.json").read_text(encoding="utf-8"))})
    res["partidas_personalizadas"] = len({r["partida"] for r in json.loads((HERE / "out" / "aram.json").read_text(encoding="utf-8"))})
    print(json.dumps(res, ensure_ascii=False))


def marcar_enviado(nome):
    """Chamar depois de subir out/<nome>.json para a página."""
    sent = json.loads(ENVIADO.read_text(encoding="utf-8")) if ENVIADO.exists() else {}
    sent[nome] = sha(HERE / "out" / f"{nome}.json")
    ENVIADO.write_text(json.dumps(sent), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "enviado":
        for n in sys.argv[2:]:
            marcar_enviado(n)
        print("ok")
    else:
        try:
            main()
        except Exception:
            traceback.print_exc()
            print(json.dumps({"ok": False, "erro": "falha inesperada, ver traceback acima"}))
