"""Coletor das personalizadas (3x3 a 5x5, qualquer mapa), lidas do cliente do LoL (LCU).

Roda sozinho a cada 10 min pelo Agendador de Tarefas do Windows. Se o cliente
estiver fechado, não lê nada. Guarda cada partida em matches/custom/<gameId>.json
e envia as novas para o GitHub (o envio dispara a atualização do site).

Funciona com várias pessoas coletando ao mesmo tempo (Defender, Teteuz, Leozin...):
antes de coletar e de enviar, baixa o que os outros já mandaram, e uma partida que
já está no GitHub não é enviada de novo.
"""
import base64, json, re, ssl, subprocess, sys, urllib.request, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "matches" / "custom"
LOG = HERE / "logs" / "coletor.log"
LOCKFILES = [Path(r"C:\Riot Games\League of Legends\lockfile"),
             Path(r"D:\Riot Games\League of Legends\lockfile"),
             Path(r"C:\Program Files\Riot Games\League of Legends\lockfile"),
             Path(r"C:\Program Files (x86)\Riot Games\League of Legends\lockfile")]
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
SEM_JANELA = 0x08000000 if sys.platform == "win32" else 0


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M} {msg}\n")


def _credenciais():
    """(porta, senha, protocolo) do cliente aberto, ou None. Tenta o lockfile e, se o LoL
    estiver instalado em outra pasta, lê a linha de comando do processo do cliente."""
    for lf in LOCKFILES:
        if lf.exists():
            _, _, port, pw, proto = lf.read_text().split(":")
            return port, pw, proto
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-CimInstance Win32_Process -Filter \"name='LeagueClientUx.exe'\").CommandLine"],
                           capture_output=True, text=True, timeout=20, creationflags=SEM_JANELA)
        cmd = r.stdout
        port = re.search(r"--app-port=(\d+)", cmd); pw = re.search(r"--remoting-auth-token=([\w-]+)", cmd)
        if port and pw:
            return port.group(1), pw.group(1), "https"
    except Exception:
        pass
    return None


def lcu():
    cred = _credenciais()
    if not cred:
        return None
    port, pw, proto = cred
    auth = base64.b64encode(f"riot:{pw}".encode()).decode()
    def get(path):
        req = urllib.request.Request(f"{proto}://127.0.0.1:{port}{path}", headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, context=CTX, timeout=15) as r:
            return json.load(r)
    return get


def is_custom(g):
    return g.get("gameType") == "CUSTOM_GAME"


def main():
    get = lcu()
    if not get:
        return 0  # cliente fechado
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        hist = get("/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=49")
    except Exception as e:  # cliente abrindo/fechando
        log(f"histórico indisponível: {e}"); return 0
    games = hist.get("games", {}).get("games", [])
    champs = None
    new = 0
    for g in games:
        if not is_custom(g):
            continue
        f = OUT / f"{g['gameId']}.json"
        if f.exists():
            continue  # já coletada por você ou por outra pessoa do grupo
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
    return new


def git(*args):
    r = subprocess.run(["git", "-C", str(HERE), *args], capture_output=True, text=True, creationflags=SEM_JANELA)
    return r.returncode, (r.stdout + r.stderr).strip()


def _atualizar_local():
    """Traz o que os outros já enviaram. Se der conflito, desiste sem estragar nada."""
    code, out = git("pull", "--rebase", "--autostash")
    if code != 0:
        git("rebase", "--abort")
    return code == 0


def sincronizar():
    """Chamar antes de coletar: assim o coletor já sabe quais partidas os outros mandaram."""
    if (HERE / ".git").exists():
        _atualizar_local()


def enviar():
    """Manda para o GitHub as personalizadas que ainda não estão lá. Se falhar, tenta na próxima rodada."""
    if not (HERE / ".git").exists():
        return
    git("fetch", "--quiet")
    # partidas novas daqui que outra pessoa já enviou: apaga a cópia local (vem pelo pull)
    _, novos = git("status", "--porcelain", "--untracked-files=all", "--", "matches/custom")
    for linha in novos.splitlines():
        if linha.startswith("??"):
            caminho = linha[3:].strip()
            if git("cat-file", "-e", f"origin/main:{caminho}")[0] == 0:
                (HERE / caminho).unlink(missing_ok=True)
    _atualizar_local()
    _, pend = git("status", "--porcelain", "--untracked-files=all", "--", "matches/custom")
    if pend:
        quem = git("config", "user.name")[1] or "coletor"
        git("add", "--", "matches/custom")
        git("commit", "-m", f"Personalizadas novas (coletor de {quem})")
    _, st = git("status", "-sb")
    if "ahead" not in (st.splitlines() or [""])[0]:
        return
    for tentativa in range(2):  # se outra pessoa enviou no mesmo instante, atualiza e tenta de novo
        code, out = git("push")
        if code == 0:
            log("enviado para o GitHub"); return
        _atualizar_local()
    log(f"falha ao enviar para o GitHub: {out[-300:]}")


if __name__ == "__main__":
    try:
        sincronizar()
    except Exception as e:
        log(f"erro ao sincronizar: {e!r}")
    try:
        main()
    except Exception as e:
        log(f"erro: {e!r}")
    try:
        enviar()
    except Exception as e:
        log(f"erro ao enviar: {e!r}")
