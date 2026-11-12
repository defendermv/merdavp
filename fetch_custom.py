"""Coletor das personalizadas (3x3 a 5x5, qualquer mapa), lidas do cliente do LoL (LCU).

Roda sozinho a cada 10 min pelo Agendador de Tarefas do Windows. Se o cliente
estiver fechado, não lê nada. Guarda cada partida em matches/custom/<gameId>.json
e envia as novas para o GitHub (o envio dispara a atualização do site).
"""
import base64, json, ssl, subprocess, sys, urllib.request, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "matches" / "custom"
LOG = HERE / "logs" / "coletor.log"
LOCKFILES = [Path(r"C:\Riot Games\League of Legends\lockfile")]
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M} {msg}\n")


def lcu():
    for lf in LOCKFILES:
        if lf.exists():
            _, _, port, pw, proto = lf.read_text().split(":")
            auth = base64.b64encode(f"riot:{pw}".encode()).decode()
            def get(path):
                req = urllib.request.Request(f"{proto}://127.0.0.1:{port}{path}",
                                             headers={"Authorization": f"Basic {auth}"})
                with urllib.request.urlopen(req, context=CTX, timeout=15) as r:
                    return json.load(r)
            return get
    return None


def is_custom(g):
    return g.get("gameType") == "CUSTOM_GAME"


def main():
    get = lcu()
    if not get:
        return  # cliente fechado
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        hist = get("/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=49")
    except Exception as e:  # cliente abrindo/fechando
        log(f"histórico indisponível: {e}"); return
    games = hist.get("games", {}).get("games", [])
    champs = None
    new = 0
    for g in games:
        if not is_custom(g):
            continue
        f = OUT / f"{g['gameId']}.json"
        if f.exists():
            continue
        full = get(f"/lol-match-history/v1/games/{g['gameId']}")
        if len(full.get("participants", [])) < 4:
            continue  # ignora 1x1 e salas de teste
        if champs is None:
            champs = {c["id"]: c["name"] for c in get("/lol-game-data/assets/v1/champion-summary.json")}
        for p in full["participants"]:
            p["championName"] = champs.get(p["championId"], str(p["championId"]))
        f.write_text(json.dumps(full, ensure_ascii=False), encoding="utf-8")
        new += 1
    if new:
        log(f"{new} personalizada(s) nova(s) salva(s)")


def git(*args):
    flags = 0x08000000 if sys.platform == "win32" else 0  # sem janela no Windows
    r = subprocess.run(["git", "-C", str(HERE), *args], capture_output=True, text=True, creationflags=flags)
    return r.returncode, (r.stdout + r.stderr).strip()


def enviar():
    """Manda para o GitHub as personalizadas que ainda não foram. Tenta de novo na próxima rodada se falhar."""
    if not (HERE / ".git").exists():
        return
    _, pend = git("status", "--porcelain", "--", "matches/custom")
    if pend:
        git("add", "--", "matches/custom")
        git("commit", "-m", "Personalizadas novas (coletor do PC)")
    _, st = git("status", "-sb")
    if "ahead" not in st.splitlines()[0]:
        return
    code, out = git("pull", "--rebase", "--autostash")
    if code == 0:
        code, out = git("push")
    log("enviado para o GitHub" if code == 0 else f"falha ao enviar para o GitHub: {out[-300:]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"erro: {e!r}")
    try:
        enviar()
    except Exception as e:
        log(f"erro ao enviar: {e!r}")
