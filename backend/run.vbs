On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")

' Starts the Python Uvicorn backend completely hidden (0)
WshShell.Run "cmd.exe /c cd C:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\backend && python -m uvicorn main:app --port 8000", 0, False

' Give the backend exactly 4 seconds to instantiate the Firebird drivers and SQLite
WScript.Sleep 4000

' Try Chrome App Mode
Err.Clear
WshShell.Run "chrome.exe --app=http://localhost:8000/", 1, False

' If Chrome fails (not found), try Edge App Mode
If Err.Number <> 0 Then
    Err.Clear
    WshShell.Run "msedge.exe --app=http://localhost:8000/", 1, False
    
    ' If both fail, just open default browser normally
    If Err.Number <> 0 Then
        Err.Clear
        WshShell.Run "http://localhost:8000/", 1, False
    End If
End If
