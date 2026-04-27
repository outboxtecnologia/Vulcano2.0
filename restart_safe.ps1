$ports = @(8000, 8080, 5173)
foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            $pid_to_kill = $conn.OwningProcess
            if ($pid_to_kill -ne 0) {
                Write-Host "Killing process on port $port with PID $pid_to_kill"
                Stop-Process -Id $pid_to_kill -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Host "No process found on port $port"
    }
}
Write-Host "Iniciando sistema..."
Start-Process -FilePath "C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\1_Subir_Questor_Explorer.bat"
