$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetScript = Join-Path $root "start.ps1"

if (!(Test-Path $targetScript)) {
  throw "Arquivo não encontrado: $targetScript"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Questor Explorer.lnk"

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)

$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-NoProfile -NoExit -ExecutionPolicy Bypass -File `"$targetScript`""
$sc.WorkingDirectory = $root
$sc.WindowStyle = 1
$sc.Description = "Abrir Questor Explorer (backend + frontend)"

# Ícone (opcional): usa o do PowerShell
$sc.IconLocation = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe,0"

$sc.Save()

Write-Host "Atalho criado em: $shortcutPath"
Write-Host "Dica: se o Windows bloquear, clique com botão direito > Propriedades > Desbloquear (se aparecer)."

