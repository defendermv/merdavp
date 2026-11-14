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
Ele cria o coletor automático e os atalhos **"Atualizar ARAM"** e **"Atualizar Flex"** na área de trabalho e no Menu Iniciar.

**Já tinha instalado antes?** Rode só o comando acima de novo para ganhar o atalho "Atualizar Flex".

## Pronto! Como usar
- **Automático:** com o cliente do LoL aberto, a cada 10 minutos as personalizadas novas vão para o site sozinhas. As flex o site busca sozinho a cada 10 minutos.
- **Na hora (personalizada):** depois da partida, clique em **Atualizar ARAM**. Aparece uma mensagem dizendo quantas partidas foram enviadas.
- **Na hora (flex):** clique em **Atualizar Flex**. Ele pede ao GitHub para buscar as flex novas e mostra quantas entraram (leva uns 30 a 60 segundos e não precisa do cliente aberto).
- Se a mesma partida for enviada por duas pessoas, ela entra só uma vez.
- Para desinstalar: apague a pasta `MerdaVP`, os atalhos, e no PowerShell rode
  `Unregister-ScheduledTask -TaskName 'MerdaVP - coletor de personalizadas'`
