# MerdaVP

Ranking do pior da semana do grupo no League of Legends.

Site: https://defendermv.github.io/merdavp/

## Como funciona

- **Flex:** o GitHub Actions (`.github/workflows/atualizar.yml`) roda a cada 10 minutos, busca as flex novas na API da Riot (`fetch_flex.py`), recalcula tudo (`build_data.py`), monta o site em `docs/` (`build_site.py`) e publica no GitHub Pages.
- **Atualizar na hora:** aba **Actions** → **Atualizar MerdaVP** → **Run workflow**.
- **Personalizadas:** o coletor (`fetch_custom.py`) roda no PC do Defender a cada 10 minutos, lê o histórico do cliente do LoL e envia as partidas novas para este repositório; o envio dispara a atualização do site.
- **Chave da Riot:** guardada em *Settings → Secrets and variables → Actions* como `RIOT_API_KEY`. Nunca vai para o código.
- **Página:** o código fica em `page/index.html`; `site/runtime.js` faz ela funcionar como site estático.
- **Regras e jogadores:** `players.json` (Riot IDs, data de início, regra do MVP).
