"""Atalho "Atualizar Flex": aperta o "Run workflow" do GitHub (busca as flex novas na Riot e
republica o site), espera terminar e mostra quantas partidas novas entraram.

Precisa do GitHub CLI (gh) logado numa conta com permissão no repositório.
Feito para rodar com pythonw: mostra uma janelinha com o andamento.
"""
import calendar, json, shutil, subprocess, sys, threading, time
import tkinter as tk
from pathlib import Path

HERE = Path(__file__).parent
REPO = "defendermv/merdavp"
SEM_JANELA = 0x08000000 if sys.platform == "win32" else 0
GH = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"


def rodar(*args, timeout=60):
    r = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout, creationflags=SEM_JANELA, cwd=HERE)
    return r.returncode, (r.stdout + r.stderr).strip()


def contar_flex():
    rodar("git", "-C", str(HERE), "pull", "--rebase", "--autostash", "--quiet")
    return len(list((HERE / "matches" / "flex").glob("*.json")))


def trabalho(status, fim):
    try:
        if not Path(GH).exists():
            return fim("Não achei o GitHub CLI (gh). Instale com:\nwinget install -e --id GitHub.cli", True)
        status("Conferindo as partidas que já estão no site…")
        antes = contar_flex()
        inicio = time.time()
        status("Pedindo ao GitHub para buscar as flex novas…")
        code, out = rodar(GH, "workflow", "run", "atualizar.yml", "-R", REPO)
        if code != 0:
            return fim(f"O GitHub recusou o pedido:\n{out[-300:]}", True)
        run_id = None
        for _ in range(30):  # acha a execução que acabou de começar
            time.sleep(3)
            code, out = rodar(GH, "run", "list", "-R", REPO, "--workflow", "atualizar.yml", "--event", "workflow_dispatch",
                              "--limit", "3", "--json", "databaseId,createdAt,status,conclusion")
            if code == 0:
                for r in json.loads(out or "[]"):
                    t = calendar.timegm(time.strptime(r["createdAt"], "%Y-%m-%dT%H:%M:%SZ"))  # horário do GitHub é UTC
                    if t >= inicio - 60:
                        run_id = r["databaseId"]; break
            if run_id:
                break
        if not run_id:
            return fim("O pedido foi feito, mas não achei a execução no GitHub.\nConfira em github.com/defendermv/merdavp/actions", True)
        status("Buscando as flex na Riot e montando o site…")
        for _ in range(100):  # até ~5 minutos
            time.sleep(3)
            code, out = rodar(GH, "run", "view", str(run_id), "-R", REPO, "--json", "status,conclusion")
            if code == 0:
                r = json.loads(out)
                if r["status"] == "completed":
                    if r["conclusion"] != "success":
                        return fim(f"A atualização terminou com erro ({r['conclusion']}).\nVeja em github.com/defendermv/merdavp/actions", True)
                    novas = contar_flex() - antes
                    if novas > 0:
                        return fim(f"{novas} flex nova(s) no site!\n\nRecarregue a página para ver.", False)
                    return fim("Nenhuma flex nova na Riot.\nO site já está em dia.", False)
        fim("A atualização está demorando mais que o normal.\nConfira em github.com/defendermv/merdavp/actions", True)
    except Exception as e:
        fim(f"Algo deu errado:\n{e}", True)


def main():
    root = tk.Tk()
    root.title("MerdaVP · Atualizar Flex")
    root.configure(bg="#0b1117")
    root.resizable(False, False)
    ico = HERE / "atualizar_aram.ico"
    if ico.exists():
        try: root.iconbitmap(str(ico))
        except Exception: pass
    tk.Label(root, text="ATUALIZAR FLEX", bg="#0b1117", fg="#85fd05", font=("Segoe UI", 13, "bold")).pack(padx=28, pady=(18, 6))
    msg = tk.Label(root, text="Começando…", bg="#0b1117", fg="#e6ecf2", font=("Segoe UI", 10), justify="center", wraplength=340)
    msg.pack(padx=28, pady=(0, 14))
    btn = tk.Button(root, text="OK", command=root.destroy, state="disabled", bg="#85fd05", fg="#0b1117",
                    activebackground="#a6ff3a", relief="flat", font=("Segoe UI", 10, "bold"), width=12)
    btn.pack(pady=(0, 18))
    root.update_idletasks()
    w, h = 400, root.winfo_reqheight()
    root.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}")
    root.attributes("-topmost", True)

    def status(t):
        root.after(0, lambda: msg.config(text=t))

    def fim(t, erro):
        def f():
            msg.config(text=t, fg="#ff8a80" if erro else "#e6ecf2")
            btn.config(state="normal"); btn.focus_set()
        root.after(0, f)

    threading.Thread(target=trabalho, args=(status, fim), daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
