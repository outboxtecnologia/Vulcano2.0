import main
for route in main.app.routes:
    if "api/agentes" in getattr(route, "path", ""):
        print(route.path, route.methods)
