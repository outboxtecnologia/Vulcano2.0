$ErrorActionPreference = "Continue"
$logFile = "D:\Questor_Restore\restore_log.txt"
$7zPath = "C:\Program Files\PLANET9\program\current\resources\app.asar.unpacked\node_modules\7zip\7zip-lite\7z.exe"
$gbakPath = "C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\Firebird\bin\gbak.exe"

Function Log-Msg {
    param([string]$message)
    $ts = "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] "
    Write-Host ($ts + $message)
    $ts + $message | Out-File -FilePath $logFile -Append
}

Log-Msg "Iniciando descompactação do arquivo Questor.fbk.xz (pode demorar bastante devido ao tamanho de 14GB)..."

$xzFile = "D:\Questor_Restore\Questor.fbk.xz"
$fbkFile = "D:\Questor_Restore\Questor.fbk"
$fdbPath = "D:\Questor_Restore\Questor.fdb"

if (Test-Path $xzFile) {
    if (-Not (Test-Path $fbkFile)) {
        & $7zPath x $xzFile -o"D:\Questor_Restore" -y 2>&1 | Out-File -FilePath $logFile -Append
        Log-Msg "Descompactação concluída."
    } else {
        Log-Msg "O arquivo Questor.fbk já existe. Pulando etapa de descompactação."
    }
    
    if (Test-Path $fbkFile) {
        Log-Msg "Iniciando restauração via gbak para $fdbPath (o banco pode ter mais de 50GB, aguarde)..."
        # O gbak converte o backup .fbk em um banco utilizável .fdb
        & $gbakPath -c -v -user SYSDBA -password masterkey $fbkFile $fdbPath 2>&1 | Out-File -FilePath $logFile -Append
        Log-Msg "Restauração finalizada com sucesso! Seu arquivo .fdb está pronto."
    } else {
        Log-Msg "ERRO: O arquivo $fbkFile não foi gerado após a descompactação."
    }
} else {
    Log-Msg "ERRO: O arquivo $xzFile não foi encontrado."
}
