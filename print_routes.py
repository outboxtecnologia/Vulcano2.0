import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import app

for route in app.routes:
    if hasattr(route, "methods"):
        print(f"{route.path} - {route.methods}")
    else:
        print(f"{route.path} - (no methods)")
