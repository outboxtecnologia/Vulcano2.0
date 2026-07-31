On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")

Dim FSO
Set FSO = CreateObject("Scripting.FileSystemObject")
Dim rootDir, targetDir
rootDir = FSO.GetParentFolderName(WScript.ScriptFullName)
targetDir = rootDir & "\backend"

' Firebird 2.5 local (banco vulcano legado, kit em firebird25\, FDB em dados\):
' sobe escondido se a porta 3050 estiver livre. Espera (True) antes de seguir.
If FSO.FileExists(rootDir & "\firebird25\bin\fbserver.exe") Then
    WshShell.Run "cmd.exe /c netstat -aon | findstr "":3050 "" | findstr LISTENING >nul || start """" /MIN """ & rootDir & "\firebird25\bin\fbserver.exe"" -a", 0, True
End If

' Starts the Python Uvicorn backend completely hidden (0) usando o ambiente virtual COM reload automático
' Porta 6060: a 8000 e do Conciliador (WSL, rede espelhada) e o Chrome bloqueia a 6000 (ERR_UNSAFE_PORT).
WshShell.Run "cmd.exe /c cd """ & targetDir & """ && " & Chr(34) & ".\.venv\Scripts\python.exe" & Chr(34) & " -m uvicorn main:app --port 6060 --reload", 0, False

' Give the backend 4 seconds to instantiate the Firebird drivers and SQLite
WScript.Sleep 4000

' Try Chrome App Mode
Err.Clear
WshShell.Run "chrome.exe --app=http://localhost:6060/index.html", 1, False

If Err.Number <> 0 Then
    Err.Clear
    WshShell.Run "msedge.exe --app=http://localhost:6060/index.html", 1, False
    
    If Err.Number <> 0 Then
        Err.Clear
        WshShell.Run "http://localhost:6060/index.html", 1, False
    End If
End If
