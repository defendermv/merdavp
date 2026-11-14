"""Atalho "Atualizar ARAM": busca as personalizadas novas no cliente do LoL, envia para o
GitHub (o que atualiza o site) e mostra uma mensagem com o resultado.

Feito para rodar com pythonw (sem janela de terminal).
"""
import ctypes, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import fetch_custom as fc

TITULO = "MerdaVP · Atualizar ARAM"


def aviso(texto, erro=False):
    # 0x40 = ícone de informação, 0x10 = ícone de erro, 0x40000 = sempre na frente
    ctypes.windll.user32.MessageBoxW(0, texto, TITULO, (0x10 if erro else 0x40) | 0x40000)


def main():
    if not fc.lcu():
        aviso("O cliente do LoL está fechado.\n\nAbra o cliente e tente de novo: as personalizadas só "
              "ficam no histórico dele.", erro=True)
        return
    try:
        fc.sincronizar()  # traz o que os outros do grupo já enviaram
    except Exception:
        pass
    antes = {f.name for f in fc.OUT.glob("*.json")} if fc.OUT.exists() else set()
    try:
        fc.main()
    except Exception as e:
        aviso(f"Não consegui ler o histórico do cliente:\n{e}", erro=True)
        return
    novas = len({f.name for f in fc.OUT.glob("*.json")} - antes)
    try:
        fc.enviar()
    except Exception as e:
        aviso(f"Salvei {novas} partida(s), mas não consegui enviar para o GitHub:\n{e}", erro=True)
        return
    _, st = fc.git("status", "-sb")
    pendente = "ahead" in (st.splitlines() or [""])[0]
    if pendente:
        aviso(f"Salvei {novas} partida(s) nova(s), mas o envio para o GitHub falhou.\n"
              "Ele tenta de novo sozinho em até 10 minutos.", erro=True)
    elif novas:
        aviso(f"{novas} personalizada(s) nova(s) enviada(s)!\n\nO site atualiza em menos de 1 minuto.")
    else:
        aviso("Nenhuma personalizada nova no histórico do cliente.\nO site já está em dia.")


if __name__ == "__main__":
    main()
