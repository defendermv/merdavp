# Cria no Agendador de Tarefas do Windows o coletor das personalizadas do MerdaVP.
# Roda fetch_custom.py a cada 10 minutos, sem janela. Com o cliente do LoL fechado, ele não faz nada.
# Para remover depois: Unregister-ScheduledTask -TaskName 'MerdaVP - coletor de personalizadas'

$app = $PSScriptRoot
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = Join-Path (Split-Path (Get-Command python.exe).Source) 'pythonw.exe' }

$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$app\fetch_custom.py`"" -WorkingDirectory $app
$trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName 'MerdaVP - coletor de personalizadas' `
  -Description 'Salva as personalizadas do LoL a partir do histórico do cliente (só age com o cliente aberto).' `
  -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null

Write-Host "Coletor instalado. Ele roda a cada 10 minutos e salva em $app\matches\custom"
