import subprocess, sys, os

os.chdir(r"C:\projetos\Vulcano2.0\backend")
python = r"C:\projetos\Vulcano2.0\backend\.venv\Scripts\python.exe"

result = subprocess.run(
    [python, "-m", "uvicorn", "main:app",
     "--host", "127.0.0.1", "--port", "6000",
     "--log-level", "info"],
    capture_output=True, text=True, timeout=20
)
print("STDOUT:", result.stdout[-3000:] if result.stdout else "(vazio)")
print("STDERR:", result.stderr[-3000:] if result.stderr else "(vazio)")
print("EXIT:", result.returncode)
