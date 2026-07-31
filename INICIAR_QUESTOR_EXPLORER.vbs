On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")

Dim FSO
Set FSO = CreateObject("Scripting.FileSystemObject")
Dim targetDir
targetDir = FSO.GetParentFolderName(WScript.ScriptFullName) & "\backend"

' Starts the Python Uvicorn backend completely hidden (0) usando o ambiente virtual COM reload automático
' Porta 6000: a 8000 e ocupada pela API do Conciliador (WSL, rede espelhada) nesta maquina.
WshShell.Run "cmd.exe /c cd """ & targetDir & """ && " & Chr(34) & ".\.venv\Scripts\python.exe" & Chr(34) & " -m uvicorn main:app --port 6000 --reload", 0, False

' Give the backend 4 seconds to instantiate the Firebird drivers and SQLite
WScript.Sleep 4000

' Try Chrome App Mode
Err.Clear
WshShell.Run "chrome.exe --app=http://localhost:6000/index.html", 1, False

If Err.Number <> 0 Then
    Err.Clear
    WshShell.Run "msedge.exe --app=http://localhost:6000/index.html", 1, False
    
    If Err.Number <> 0 Then
        Err.Clear
        WshShell.Run "http://localhost:6000/index.html", 1, False
    End If
End If
