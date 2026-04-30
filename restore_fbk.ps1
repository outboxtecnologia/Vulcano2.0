$ErrorActionPreference = "Continue"
$logFile = "D:\Questor_Restore\restore_log_fase2.txt"
$gbakPath = "C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\Firebird\bin\gbak.exe"

Function Log-Msg {
    param([string]$message)
    $ts = "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] "
    Write-Host ($ts + $message)
    $ts + $message | Out-File -FilePath $logFile -Append
}

$fbkFile = "D:\Questor_Restore\Questor.fbk"
$fdbPath = "D:\Questor_Restore\Questor.fdb"

Log-Msg "Limpando o arquivo .FDB corrompido/incompleto..."
if (Test-Path $fdbPath) {
    Remove-Item -Path $fdbPath -Force
}

if (Test-Path $fbkFile) {
    Log-Msg "Iniciando a restauração do banco de dados (Apenas Fase 2 - gbak)..."
    Log-Msg "Tamanho do arquivo FBK de origem: $([math]::Round((Get-Item $fbkFile).Length / 1GB, 2)) GB"
    
    # O gbak converte o backup .fbk em um banco utilizável .fdb
    & $gbakPath -c -v -user SYSDBA -password masterkey $fbkFile $fdbPath 2>&1 | Out-File -FilePath $logFile -Append
    
    Log-Msg "Restauração finalizada com sucesso! Seu arquivo .fdb está pronto."
} else {
    Log-Msg "ERRO: O arquivo $fbkFile não foi encontrado."
}
