# Instalador do coletor de personalizadas do MerdaVP (para amigos do grupo).
# Uso, depois de clonar o repositório:
#   powershell -ExecutionPolicy Bypass -File "$HOME\MerdaVP\instalar_amigo.ps1"
$ErrorActionPreference = 'Stop'
$app = $PSScriptRoot
Write-Host "== MerdaVP: instalando o coletor de personalizadas ==" -ForegroundColor Green

function Exige($nome, $cmd, $dica) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "Falta o $nome. Instale com:  $dica" -ForegroundColor Red
    Write-Host "Depois feche e abra o PowerShell e rode este instalador de novo."
    exit 1
  }
}
Exige 'Git' 'git' 'winget install -e --id Git.Git'
Exige 'GitHub CLI' 'gh' 'winget install -e --id GitHub.cli'
Exige 'Python' 'python' 'winget install -e --id Python.Python.3.12'

# Python sem janela (pythonw) para o coletor rodar escondido
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = Join-Path (Split-Path (Get-Command python).Source) 'pythonw.exe' }
if (-not (Test-Path $py)) { Write-Host "Não achei o pythonw.exe. Reinstale o Python." -ForegroundColor Red; exit 1 }

# Login no GitHub
gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Você ainda não entrou no GitHub. Rode:  gh auth login   (GitHub.com > HTTPS > Yes > Login with a web browser)" -ForegroundColor Red
  exit 1
}
gh auth setup-git | Out-Null
$login = gh api user --jq .login
$id = gh api user --jq .id
git -C $app config user.name $login
git -C $app config user.email "$id+$login@users.noreply.github.com"
Write-Host "Conta do GitHub: $login"

# Permissão para enviar partidas
$pode = gh api repos/defendermv/merdavp --jq .permissions.push 2>$null
if ($pode -ne 'true') {
  Write-Host "Atenção: sua conta ainda não pode enviar partidas. Peça ao Defender o convite de colaborador" -ForegroundColor Yellow
  Write-Host "e aceite em https://github.com/defendermv/merdavp/invitations . O resto vai ficar instalado." -ForegroundColor Yellow
}

# Coletor automático a cada 10 minutos (só age com o cliente do LoL aberto)
$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$app\fetch_custom.py`"" -WorkingDirectory $app
$trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'MerdaVP - coletor de personalizadas' `
  -Description 'Salva as personalizadas do LoL e envia para o site do MerdaVP (só age com o cliente aberto).' `
  -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Coletor automático instalado (a cada 10 minutos)."

# Atalho "Atualizar ARAM" na área de trabalho e no Menu Iniciar
$ws = New-Object -ComObject WScript.Shell
foreach ($pasta in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) {
  $lnk = $ws.CreateShortcut((Join-Path $pasta 'Atualizar ARAM.lnk'))
  $lnk.TargetPath = $py
  $lnk.Arguments = "`"$app\atualizar_aram.py`""
  $lnk.WorkingDirectory = $app
  $lnk.IconLocation = "$app\atualizar_aram.ico,0"
  $lnk.Description = 'Envia as personalizadas novas do LoL para o site do MerdaVP'
  $lnk.Save()
}
Write-Host "Atalho 'Atualizar ARAM' criado na área de trabalho e no Menu Iniciar."
Write-Host ""
Write-Host "Pronto! Depois de uma personalizada, deixe o cliente aberto uns minutos ou clique em 'Atualizar ARAM'." -ForegroundColor Green
