# MerdaVP: como enviar as personalizadas do seu PC

Com isso, as personalizadas que **você** jogar entram no ranking do ARAM mesmo quando o Defender não estiver na partida.
Só funciona no Windows e leva uns 10 minutos, uma vez só.

## 1. Conta no GitHub e convite
1. Crie uma conta em **github.com** (se ainda não tiver) e mande seu **nome de usuário** para o Defender.
2. Ele te convida para o projeto. Aceite o convite em: https://github.com/defendermv/merdavp/invitations

## 2. Instalar os programas (uma vez)
Abra o **PowerShell** e rode estes 3 comandos, um de cada vez:
```
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
winget install -e --id GitHub.cli
```
**Feche o PowerShell e abra de novo** (senão ele não acha os programas novos).

## 3. Entrar no GitHub
```
gh auth login
```
Responda: **GitHub.com** → **HTTPS** → **Yes** → **Login with a web browser**.
Aperte **Enter**, cole o código no navegador e autorize. Espere aparecer "Logged in as ...".

## 4. Baixar o projeto e instalar o coletor
```
gh repo clone defendermv/merdavp "$HOME\MerdaVP"
```
```
powershell -ExecutionPolicy Bypass -File "$HOME\MerdaVP\instalar_amigo.ps1"
```
Ele cria o coletor automático e o atalho **"Atualizar ARAM"** na área de trabalho.

## Pronto! Como usar
- **Automático:** com o cliente do LoL aberto, a cada 10 minutos as personalizadas novas vão para o site sozinhas.
- **Na hora:** depois da partida, clique em **Atualizar ARAM**. Aparece uma mensagem dizendo quantas partidas foram enviadas.
- Se a mesma partida for enviada por duas pessoas, ela entra só uma vez.
- Para desinstalar: apague a pasta `MerdaVP`, o atalho, e no PowerShell rode
  `Unregister-ScheduledTask -TaskName 'MerdaVP - coletor de personalizadas'`
