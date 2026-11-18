# MerdaVP

Ranking mensal do grupo no League of Legends: MVP e MerdaVP de cada temporada.

Site: https://defendermv.github.io/merdavp/

## Como funciona

- **Flex:** o GitHub Actions (`.github/workflows/atualizar.yml`) roda a cada 10 minutos, busca as flex novas na API da Riot (`fetch_flex.py`), recalcula tudo (`build_data.py`), monta o site em `docs/` (`build_site.py`) e publica no GitHub Pages.
- **Atualizar na hora:** aba **Actions** → **Atualizar MerdaVP** → **Run workflow**.
- **Personalizadas:** o coletor (`fetch_custom.py`) roda no PC de quem joga (Defender, Teteuz, Leozin) a cada 10 minutos, lê o histórico do cliente do LoL e envia as partidas novas para este repositório; o envio dispara a atualização do site. Partida enviada por duas pessoas entra uma vez só. O atalho **Atualizar ARAM** (`atualizar_aram.py`) faz o mesmo na hora.
- **Amigos enviando partidas:** veja [GUIA-AMIGOS.md](GUIA-AMIGOS.md) e o instalador `instalar_amigo.ps1`.
- **Chave da Riot:** guardada em *Settings → Secrets and variables → Actions* como `RIOT_API_KEY`. Nunca vai para o código.
- **Página:** o código fica em `page/index.html`; `site/runtime.js` faz ela funcionar como site estático.
- **Regras e jogadores:** `players.json` (Riot IDs, início das temporadas, mínimo de partidas, valores do pix, partidas anuladas).
- **Temporadas:** mensais, do dia 8 ao dia 7 do mês seguinte (a primeira vai de 16/11/2026 a 07/12/2026). Os três últimos de cada partida levam +1/+2/+3 pontos e os três primeiros tiram 3/2/1; menos pontos por partida = MVP, mais = MerdaVP. Flex e ARAM têm rankings separados. Quem tem menos de 10 partidas na temporada fica como provisório.
- **Personalizadas:** 5x5 na Summoner's Rift com 3 ou mais do grupo valem como flex; as de ARAM valem só no ranking do ARAM.
- **Número das partidas:** cada partida válida recebe um número fixo (`numeracao.json`), mostrado no placar. Para anular uma partida (queda de jogador etc.), coloque o número em `partidas_anuladas` no `players.json`: ela sai dos rankings, mas o número continua reservado.
