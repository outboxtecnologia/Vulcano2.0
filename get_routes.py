import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from main import app

for route in app.routes:
    if hasattr(route, 'path') and 'preview-baixas' in route.path:
        print(f"PATH: {route.path}")
        print(f"METHODS: {route.methods}")
